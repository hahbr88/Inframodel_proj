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
    weather_mode: Literal["mock", "snapshot", "database", "live"] = "mock"
    weather_storage: Literal["json", "database"] = "json"
    account_provider: Literal["local", "cognito"] = "local"
    cognito_region: str = "ap-northeast-2"
    cognito_user_pool_id: str = ""
    cognito_client_id: str = ""
    weather_database_batch_size: int = 1000
    weather_snapshot_retention: int = 3
    write_database_url: str = "sqlite+aiosqlite:///./integrated_was.db"
    read_database_url: str = "sqlite+aiosqlite:///./integrated_was.db"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = Field(
        default="change-this-secret-in-production",
        min_length=16,
    )
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    demo_username: str = "admin"
    demo_password: str = "password123"
    admin_username: str = "admin"
    admin_password: str = "password123"
    cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:5174,http://127.0.0.1:5174"
    )
    cors_origin_regex: str = (
        r"^https?://("
        r"localhost|127\.0\.0\.1|"
        r"10(?:\.\d{1,3}){3}|"
        r"192\.168(?:\.\d{1,3}){2}|"
        r"172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2}"
        r"):(5173|5174)$"
    )
    kma_service_key: str = ""
    kma_base_url: str = "https://apis.data.go.kr/1360000/TourStnInfoService1"
    kma_timeout_seconds: float = 5.0
    kma_snapshot_path: str = "./data/kma_snapshot.json"
    kma_collection_retries: int = 3
    kma_collection_retry_seconds: int = 5
    kma_collection_concurrency: int = 10
    kma_course_limit: int = 0
    cookie_secure: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
