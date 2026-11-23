import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware

import app.models.content  # noqa: F401
import app.models.feedback  # noqa: F401
import app.models.interview  # noqa: F401
import app.models.progress  # noqa: F401
import app.models.quiz  # noqa: F401
import app.models.revision  # noqa: F401
import app.models.submission  # noqa: F401
import app.models.user  # noqa: F401
from app.config import settings
from app.db import Base, SessionLocal, engine, get_db
from app.routers import (
    admin,
    auth,
    content,
    feedback,
    interview,
    judge,
    progress,
    quizzes,
    revision,
    tutor,
)
from app.seed import seed_admin, seed_if_changed
from app.services.session_cleanup import cleanup_expired_sessions

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure the schema exists. Note this only creates *missing tables*; it never
    # adds a column to an existing one, so a model change still needs its Alembic
    # revision applied (`alembic upgrade head`) before or with the deploy.
    Base.metadata.create_all(bind=engine)

    # Sync content when the tree changed since the last successful seed.
    #
    # The guard used to be `if problems == 0`, which meant content changes never
    # reached an existing deployment: a commit that added 134 problems sat in the
    # repository while production kept serving the old set until someone ran
    # `python -m app.seed` by hand. A content fingerprint keeps an unchanged boot
    # nearly free while making a content commit self-deploying.
    # A content problem degrades to "stale content", never to "no service".
    # Seeding is now a boot-time code path on every content change, and one
    # malformed JSON file used to raise out of the lifespan — which means uvicorn
    # never starts and the container restart-loops.
    try:
        with SessionLocal() as db:
            counts, synced = seed_if_changed(db)
            if synced:
                logging.getLogger(__name__).info("Content synced: %s", counts)
    except Exception:
        logging.getLogger(__name__).exception(
            "Content sync failed; serving the previously seeded content"
        )

    try:
        with SessionLocal() as db:
            seed_admin(db)
    except Exception:
        logging.getLogger(__name__).exception("Admin seed failed")

    async def _cleanup_loop() -> None:
        while True:
            await asyncio.sleep(21600)
            try:
                with SessionLocal() as db:
                    cleanup_expired_sessions(db)
            except Exception:
                logging.getLogger(__name__).exception("Session cleanup failed")

    try:
        with SessionLocal() as db:
            cleanup_expired_sessions(db)
    except Exception:
        logging.getLogger(__name__).exception("Session cleanup failed")
    cleanup_task = asyncio.create_task(_cleanup_loop())

    yield

    cleanup_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await cleanup_task


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["X-Frame-Options"] = "DENY"
        return response


def _payload_too_large() -> JSONResponse:
    return JSONResponse(
        status_code=413,
        content={"detail": {"code": "PAYLOAD_TOO_LARGE", "message": "Request body too large."}},
    )


class BodyLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        limit = (
            2_621_440
            if request.url.path == "/api/v1/interview/parse-resume"
            else 1_048_576
        )
        length = request.headers.get("content-length")
        if length is not None:
            try:
                parsed_length = int(length)
            except ValueError:
                parsed_length = -1
            if parsed_length > limit:
                return _payload_too_large()
            if parsed_length >= 0:
                return await call_next(request)
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > limit:
                return _payload_too_large()

        async def receive():
            return {"type": "http.request", "body": bytes(body), "more_body": False}

        return await call_next(Request(request.scope, receive=receive))


_is_prod = settings.environment.lower() == "production"

app = FastAPI(
    title="Merit API",
    version="1.0.0",
    docs_url=None if _is_prod else "/api/docs",
    redoc_url=None if _is_prod else "/api/redoc",
    openapi_url=None if _is_prod else "/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(BodyLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(auth.router)
app.include_router(progress.router)
app.include_router(judge.router)
app.include_router(content.router)
app.include_router(quizzes.router)
app.include_router(admin.router)
app.include_router(tutor.router)
app.include_router(interview.router)
app.include_router(feedback.router)
app.include_router(revision.router)


@app.get("/api/v1/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        logging.getLogger(__name__).exception("Health check database probe failed")
        return JSONResponse(status_code=503, content={"status": "error", "service": "merit-api"})
    return {"status": "ok", "service": "merit-api"}
