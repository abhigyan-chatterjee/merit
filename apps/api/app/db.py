import os
from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# The API container runs as root (apps/api/Dockerfile declares no USER) and the
# sandbox drops submissions to an unprivileged uid. Files root creates under the
# default umask are 0644 — world-readable — so submitted code could open the
# SQLite database and read every account's email and password hash. Tightening
# the umask before the engine creates anything makes the database and its
# directory owner-only, and leaves root's own access untouched.
if hasattr(os, "geteuid") and os.geteuid() == 0:
    os.umask(0o077)

# Engine configuration
connect_args = {}
engine_kwargs: dict = {"echo": False}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
elif settings.database_url.startswith("postgresql"):
    # Neon pooled connections can go stale (scale-to-zero / idle timeout);
    # pre-ping keeps prod checkouts honest. SQLite path untouched.
    engine_kwargs.update(
        pool_pre_ping=True, pool_recycle=300, pool_timeout=15, pool_size=5, max_overflow=5
    )

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    **engine_kwargs,
)

# Apply SQLite pragmas (WAL mode and foreign keys)
if settings.database_url.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
