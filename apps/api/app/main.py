import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

import app.models.content  # noqa: F401
import app.models.feedback  # noqa: F401
import app.models.progress  # noqa: F401
import app.models.quiz  # noqa: F401
import app.models.revision  # noqa: F401
import app.models.submission  # noqa: F401
import app.models.user  # noqa: F401
from app.config import settings
from app.db import Base, SessionLocal, engine
from app.routers import (
    admin,
    auth,
    content,
    feedback,
    judge,
    progress,
    quizzes,
    revision,
    tutor,
)
from app.seed import seed_if_changed

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

    yield


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["X-Frame-Options"] = "DENY"
        return response


app = FastAPI(
    title="Merit API",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(progress.router)
app.include_router(judge.router)
app.include_router(content.router)
app.include_router(quizzes.router)
app.include_router(admin.router)
app.include_router(tutor.router)
app.include_router(feedback.router)
app.include_router(revision.router)


@app.get("/api/v1/health")
def health_check():
    return {"status": "ok", "service": "merit-api"}
