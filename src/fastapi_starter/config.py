"""Application settings, read from environment variables (prefix ``APP_``) and ``.env``."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

DEFAULT_UPLOAD_TYPES = frozenset(
    {
        "application/pdf",
        "text/csv",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
)


def _split_csv(value: object) -> object:
    """Allow ``APP_X=a,b,c`` in addition to JSON lists for list-valued settings."""
    if isinstance(value, str):
        value = value.strip()
        if value.startswith("["):
            import json

            return json.loads(value)
        return [item.strip() for item in value.split(",") if item.strip()]
    return value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "FastAPI Starter"
    environment: Literal["dev", "test", "prod"] = "dev"
    debug: bool = False
    log_level: str = "INFO"

    # Database: SQLite for local dev/tests, Postgres (asyncpg) in compose/production.
    database_url: str = "sqlite+aiosqlite:///./data/app.db"
    database_echo: bool = False

    # CORS: the Vite dev server of the React client runs on :5173.
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )

    # Uploads.
    upload_dir: Path = Path("data/uploads")
    max_upload_bytes: int = 10 * 1024 * 1024
    allowed_upload_types: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: sorted(DEFAULT_UPLOAD_TYPES)
    )

    # FastAPI BackgroundTasks demo writes here.
    message_log: Path = Path("data/messages.log")

    # Taskiq broker. Empty = in-process broker (dev/tests); ``redis://...`` = real worker.
    broker_url: str = ""

    # Outgoing HTTP demo (httpx).
    external_api_url: str = "https://jsonplaceholder.typicode.com"
    external_api_timeout: float = 5.0

    @field_validator("cors_origins", "allowed_upload_types", mode="before")
    @classmethod
    def _parse_list(cls, value: object) -> object:
        return _split_csv(value)

    @property
    def uses_redis_broker(self) -> bool:
        return self.broker_url.startswith(("redis://", "rediss://"))


@lru_cache
def get_settings() -> Settings:
    """Process-wide settings (cached). Tests build their own ``Settings`` instead."""
    return Settings()
