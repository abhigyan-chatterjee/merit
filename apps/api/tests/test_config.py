import pytest

from app.config import Settings


def test_development_generates_temporary_secret_when_missing(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.warns(UserWarning, match="temporary development key"):
        settings = Settings(secret_key="", environment="development")

    assert len(settings.secret_key) >= 64


def test_production_rejects_missing_secret_without_env_file(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError, match="production mode"):
        Settings(secret_key="", environment="production")


def test_production_rejects_placeholder_secret(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "replace_with_a_secure_random_key_here")

    with pytest.raises(RuntimeError, match="production mode"):
        Settings(secret_key="replace_with_a_secure_random_key_here", environment="production")


def test_sqlite_relative_url_normalized_to_apps_api():
    settings = Settings(
        secret_key="test_secret_for_config_validation_32chars",
        database_url="sqlite:///./merit.db",
    )
    assert settings.database_url.startswith("sqlite:////")
    assert settings.database_url.endswith("apps/api/merit.db")

