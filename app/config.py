# config.py
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from functools import lru_cache

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str
    DEBUG: bool
    ENVIRONMENT: str
    DATABASE_URL: str

    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    ALLOWED_ORIGINS: List[str]

    RATE_LIMIT_PER_MINUTE: int
    LOGIN_RATE_LIMIT_PER_MINUTE: int

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None, 
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
