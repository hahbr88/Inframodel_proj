from functools import lru_cache

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Integrated Weather & Course WAS"
    environment: str = "local"
    api_prefix: str = "/api"
    data_mode: Literal["mock", "database"] = "mock"
    weather_mode: Literal["mock", "snapshot", "live"] = "mock"
    write_database_url: str = "sqlite+aiosqlite:///./integrated_was.db"
    read_database_url: str = "sqlite+aiosqlite:///./integrated_was.db"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = Field(
        default="change-this-secret-in-production",
        min_length=16,
    )
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    kma_service_key: str = ""
    kma_base_url: str = (
        "https://apis.data.go.kr/1360000/TourStnInfoService1"
    )
    kma_timeout_seconds: float = 5.0
    kma_snapshot_path: str = "./data/kma_snapshot.json"
    kma_collection_retries: int = 3
    kma_collection_retry_seconds: int = 60
    kma_collection_concurrency: int = 10
    kma_course_limit: int = 0
    cookie_secure: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
