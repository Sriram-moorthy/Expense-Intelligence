import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


def _env_file() -> str | None:
    # Tests set TEST_DATABASE_URL and must not load a personal .env.
    if os.environ.get("TEST_DATABASE_URL"):
        return None
    return ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_file(),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Expense Intelligence"
    environment: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    database_url: str


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
