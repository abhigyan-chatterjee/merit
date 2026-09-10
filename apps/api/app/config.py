from typing import Any

from pydantic import model_validator
from pydantic_settings import BaseSettings

INSECURE_SECRET_KEYS = {
    "algovista_super_secret_jwt_signing_key_at_least_32_chars_long_2026",
    "change_this_to_a_secure_random_key_in_production_32chars!",
    "replace_with_a_secure_random_key_here",
    "your_secret_key_here",
    "changeme",
    "change_me",
    "secret",
}


class Settings(BaseSettings):
    app_name: str = "Algovista API"
    environment: str = "development"
    database_url: str = "sqlite:///./algovista.db"
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

    @model_validator(mode="before")
    @classmethod
    def validate_secret_key(cls, values: Any) -> Any:
        secret = None
        if isinstance(values, dict):
            secret = values.get("secret_key")
        elif hasattr(values, "secret_key"):
            secret = values.secret_key

        if not secret or not str(secret).strip():
            raise RuntimeError(
                "CRITICAL SECURITY CONFIGURATION ERROR: SECRET_KEY is missing or empty.\n"
                "A cryptographically secure SECRET_KEY must be configured via environment "
                "variable or in apps/api/.env.\n\n"
                "To generate a secure key, run:\n"
                '    python3 -c "import secrets; print(secrets.token_urlsafe(48))"\n\n'
                "Then export SECRET_KEY in your environment or place it in apps/api/.env:\n"
                "    SECRET_KEY=<generated_key>\n"
            )

        cleaned_secret = str(secret).strip()
        if cleaned_secret in INSECURE_SECRET_KEYS:
            raise RuntimeError(
                "CRITICAL SECURITY CONFIGURATION ERROR: SECRET_KEY is set to an insecure "
                f"placeholder ({cleaned_secret!r}).\n"
                "A cryptographically secure SECRET_KEY must be configured via environment "
                "variable or in apps/api/.env.\n\n"
                "To generate a secure key, run:\n"
                '    python3 -c "import secrets; print(secrets.token_urlsafe(48))"\n\n'
                "Then export SECRET_KEY in your environment or place it in apps/api/.env:\n"
                "    SECRET_KEY=<generated_key>\n"
            )

        return values


settings = Settings()
