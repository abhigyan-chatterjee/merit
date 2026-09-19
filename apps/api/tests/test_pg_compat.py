"""Neon Postgres prod-readiness compat checks.

Runs WITHOUT a live server: engines are built but never connected, DDL is
compiled against the Postgres dialect, and migrations are inspected (never
executed live).
"""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from app.config import Settings

# Placeholder credentials only — never a real URL, never committed secrets.
PG_URL = (
    "postgresql+psycopg://merit:placeholder-secret"
    "@ep-test-123456.us-east-2.aws.neon.tech/merit?sslmode=require"
)

SECRET = "test_secret_for_pg_compat_validation_32chars"


def test_postgres_url_passes_through_untouched():
    settings = Settings(secret_key=SECRET, database_url=PG_URL)
    assert settings.database_url == PG_URL


def test_sqlite_default_unchanged_without_env():
    settings = Settings(
        secret_key=SECRET,
        database_url="sqlite:///./merit.db",
    )
    assert settings.database_url.startswith("sqlite:////")
    assert settings.database_url.endswith("apps/api/merit.db")


def test_engine_builds_from_pg_url_without_connecting():
    engine = create_engine(PG_URL)
    try:
        assert engine.dialect.name == "postgresql"
        assert engine.url.drivername == "postgresql+psycopg"
        assert engine.url.query.get("sslmode") == "require"
    finally:
        engine.dispose()


def test_metadata_compiles_on_postgres_dialect():
    import app.models.content  # noqa: F401 (register tables)
    import app.models.progress  # noqa: F401
    import app.models.quiz  # noqa: F401
    import app.models.submission  # noqa: F401
    import app.models.user  # noqa: F401
    from app.db import Base

    dialect = postgresql.dialect()
    assert len(Base.metadata.tables) > 0
    for table in Base.metadata.sorted_tables:
        ddl = str(CreateTable(table).compile(dialect=dialect))
        assert f"CREATE TABLE {table.name}" in ddl
        # Every index must carry a deterministic name (PG needs names for
        # DROP/CREATE INDEX round-trips via batch_op.f()).
        for index in table.indexes:
            assert index.name, f"unnamed index on {table.name}"


def test_migration_chain_has_clean_upgrade_paths_and_no_sqlite_ddl():
    api_dir = Path(__file__).resolve().parent.parent
    cfg = Config()
    cfg.set_main_option("script_location", str(api_dir / "alembic"))
    script = ScriptDirectory.from_config(cfg)

    revisions = list(script.walk_revisions())
    assert len(revisions) > 0
    heads = script.get_heads()
    assert len(heads) == 1  # single linear chain, no branches

    for rev in revisions:
        assert callable(getattr(rev.module, "upgrade", None)), rev.revision
        assert callable(getattr(rev.module, "downgrade", None)), rev.revision
        source = (Path(rev.path)).read_text().upper()
        # Strip SQLAlchemy-level autoincrement=True kwargs (render as
        # IDENTITY/SERIAL on PG) so only raw SQLite DDL keywords can match.
        source = source.replace("AUTOINCREMENT=TRUE", "")
        for sqlite_only in ("PRAGMA", "AUTOINCREMENT", "SQLITE_"):
            assert sqlite_only not in source, f"{sqlite_only} in {rev.revision}"

    # Clerk migration must apply cleanly on PG: unique *index* (not a table
    # constraint) on nullable clerk_id — PG unique indexes permit multiple
    # NULLs, matching SQLite semantics.
    clerk = script.get_revision("c4f1a2b3d4e5")
    assert clerk is not None
    clerk_source = Path(clerk.path).read_text()
    assert 'op.create_index("uq_users_clerk_id"' in clerk_source
