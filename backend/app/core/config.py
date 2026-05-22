from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RouteCraft Backend"
    app_env: str = "local"
    app_host: str = "0.0.0.0"
    app_port: int = 3002
    api_v1_prefix: str = "/api/v1"
    cors_allow_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3003",
            "http://127.0.0.1:3003",
            "http://localhost:3004",
            "http://127.0.0.1:3004",
        ]
    )
    cors_allow_credentials: bool = True
    log_level: str = "INFO"
    database_url: str = "mysql+asyncmy://root:password@localhost:3306/lushujiang?charset=utf8mb4"
    amap_api_key: str | None = None
    amap_key: str | None = None
    weather_provider: str = ""
    weather_api_key: str | None = None
    amap_weather_key: str | None = None
    realtime_provider: str = ""
    realtime_search_api_key: str | None = None
    tavily_api_key: str | None = None
    llm_provider: str = "openai-compatible"
    llm_base_url: str | None = None
    llm_model_name: str | None = None
    llm_api_key: str | None = None
    llm_timeout_s: int = 60
    llm_max_tokens: int | None = None
    llm_temperature: float = 0.7
    llm_secret_key: str = "local-dev-llm-secret"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="BACKEND_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
