from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# Engine configuration
connect_args = {}
engine_kwargs: dict = {"echo": False}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
elif settings.database_url.startswith("postgresql"):
    # Neon pooled connections can go stale (scale-to-zero / idle timeout);
    # pre-ping keeps prod checkouts honest. SQLite path untouched.
    engine_kwargs["pool_pre_ping"] = True

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
