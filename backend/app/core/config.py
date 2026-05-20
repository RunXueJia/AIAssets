#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 09:35
# @File     : config.py
# @Desc     : Application settings.

from functools import lru_cache
import json
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    app_name: str = "24小时AI增长资产引擎"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = "change-this-secret"
    access_token_expire_seconds: int = 7200

    database_name: str = "AIdrivenGrowthAssetEngine"
    database_url: str = (
        "mysql+pymysql://root:password@127.0.0.1:3306/"
        "AIdrivenGrowthAssetEngine?charset=utf8mb4"
    )
    redis_url: str = "redis://127.0.0.1:6379/0"
    celery_broker_url: str = "redis://127.0.0.1:6379/1"
    celery_result_backend: str = "redis://127.0.0.1:6379/2"
    enable_celery_tasks: bool = False
    cors_origins: list[str] = Field(default_factory=lambda: ["http://127.0.0.1:5173", "http://localhost:5173"])
    storage_root: Path = Path("../storage")

    fetch_timeout_seconds: int = 20
    fetch_max_content_chars: int = 12000
    fetch_seed_urls: str = (
        "https://www.technologyreview.com/topic/artificial-intelligence/,"
        "https://openai.com/news/"
    )

    llm_model_provider: str = "openai_compatible"
    llm_model_base_url: str = "https://api.example.com/v1"
    llm_model_api_key: str = ""
    llm_model_name: str = ""
    llm_request_timeout_seconds: int = 60
    llm_enable_real_calls: bool = False

    ffmpeg_bin: str = "ffmpeg"
    enable_real_ffmpeg: bool = False

    default_admin_username: str = "admin"
    default_admin_password: str = "Admin123456"
    default_admin_display_name: str = "管理员"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("storage_root", mode="after")
    @classmethod
    def resolve_storage_root(cls, value: Path) -> Path:
        if value.is_absolute():
            return value
        return (BACKEND_DIR / value).resolve()

    @property
    def fetch_seed_url_list(self) -> list[str]:
        value = self.fetch_seed_urls.strip()
        if not value:
            return []
        if value.startswith("["):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                parsed = []
            return [str(item).strip() for item in parsed if str(item).strip()]
        return [item.strip() for item in value.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
