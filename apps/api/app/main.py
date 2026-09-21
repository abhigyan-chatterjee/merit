import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect
from starlette.middleware.base import BaseHTTPMiddleware

import app.models.content  # noqa: F401
import app.models.feedback  # noqa: F401
import app.models.progress  # noqa: F401
import app.models.quiz  # noqa: F401
import app.models.submission  # noqa: F401
import app.models.user  # noqa: F401
from app.config import settings
from app.db import Base, SessionLocal, engine
from app.routers import admin, auth, content, feedback, judge, progress, quizzes, tutor
from app.seed import seed_all

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database schema and verified seed content exist on startup
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    if not inspector.has_table("problems"):
        with SessionLocal() as db:
            seed_all(db)
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


@app.get("/api/v1/health")
def health_check():
    return {"status": "ok", "service": "merit-api"}
