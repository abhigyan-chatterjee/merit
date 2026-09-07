from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Algovista API"
    environment: str = "development"
    database_url: str = "sqlite:///./algovista.db"
    secret_key: str = "algovista_super_secret_jwt_signing_key_at_least_32_chars_long_2026"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


settings = Settings()
