import os

# Set a test-only SECRET_KEY before any app modules or settings are imported.
os.environ["SECRET_KEY"] = "test_only_jwt_secret_key_algovista_testing_minimum_32_chars"

from collections.abc import Generator  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import app.models.content  # noqa: E402, F401 (register all tables on Base.metadata)
import app.models.progress  # noqa: E402, F401
import app.models.quiz  # noqa: E402, F401
import app.models.submission  # noqa: E402, F401
import app.models.user  # noqa: E402, F401
from app.db import Base, get_db  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402
from app.seed import _resolve_content_dir as _content_dir  # noqa: E402

app = fastapi_app

# Shared in-memory SQLite engine for tests
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=test_engine)
    # Seed once against the TEST engine. Module fixtures call seed_all(db)
    # with the app's SessionLocal (bound to dev DATABASE_URL), so rebind it
    # here for the whole test session; per-test transactions still roll back
    # mutations via the db_session fixture.
    from app import db as app_db

    original_bind = app_db.SessionLocal.kw.get("bind")
    app_db.SessionLocal.configure(bind=test_engine)
    from app.seed import seed_paths, seed_problems, seed_questions

    with app_db.SessionLocal() as db:
        seed_problems(db, _content_dir("problems"))
        seed_questions(db, _content_dir("questions"))
        seed_paths(db, _content_dir("paths"))
        db.commit()
    yield
    app_db.SessionLocal.configure(bind=original_bind)
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
