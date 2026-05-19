from functools import lru_cache

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Hours24 Backend"
    api_v1_prefix: str = "/api/v1"
    environment: str = "local"

    database_url: str = "mysql+asyncmy://hours24:hours24_password@127.0.0.1:3306/hours24?charset=utf8mb4"
    redis_url: str = "redis://localhost:6379/0"

    object_storage_endpoint: str = "http://localhost:9000"
    object_storage_bucket: str = "hours24"
    object_storage_access_key: str = ""
    object_storage_secret_key: str = ""

    jwt_secret_key: str = "change-me-in-production-with-at-least-32-bytes"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    refresh_token_expire_minutes: int = 60 * 24 * 7

    cors_origins: list[AnyHttpUrl | str] = Field(default_factory=lambda: ["*"])
    encryption_key: str = "hours24-local-encryption-key"

    default_llm_timeout_seconds: int = 60

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
