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

        env_mode = "development"
        if isinstance(values, dict):
            env_mode = values.get("environment", "development")
        elif hasattr(values, "environment"):
            env_mode = getattr(values, "environment", "development")

        is_insecure = (
            not secret
            or not str(secret).strip()
            or str(secret).strip() in INSECURE_SECRET_KEYS
        )

        if is_insecure:
            if str(env_mode).lower() == "production":
                raise RuntimeError(
                    "CRITICAL SECURITY CONFIGURATION ERROR: In production mode, SECRET_KEY "
                    "must be configured via environment variable with a secure value.\n"
                    "Generate a secure key:\n"
                    '    python3 -c "import secrets; print(secrets.token_urlsafe(48))"\n'
                )

            # In development, auto-generate a secure random secret so local dev works smoothly
            import secrets
            dev_key = secrets.token_urlsafe(48)
            import warnings
            warnings.warn(
                "SECRET_KEY not set or using placeholder; generated a temporary development key. "
                "Set SECRET_KEY in apps/api/.env for persistent sessions.",
                UserWarning,
                stacklevel=2,
            )
            if isinstance(values, dict):
                values["secret_key"] = dev_key
            else:
                values.secret_key = dev_key

        return values

    @model_validator(mode="after")
    def normalize_sqlite_url(self) -> "Settings":
        if (
            self.database_url.startswith("sqlite:///")
            and not self.database_url.startswith("sqlite:////")
            and ":memory:" not in self.database_url
        ):
            from pathlib import Path

            rel_path = self.database_url[len("sqlite:///") :]
            if rel_path.startswith("./"):
                rel_path = rel_path[2:]
            api_dir = Path(__file__).resolve().parent.parent
            abs_db_path = (api_dir / rel_path).resolve()
            self.database_url = f"sqlite:///{abs_db_path}"
        return self


settings = Settings()
