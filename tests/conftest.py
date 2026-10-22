"""Shared fixtures: a temp SQLite database, temp upload dir, mocked upstream HTTP, no Redis."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import httpx2
import pytest

# Make sure nothing from the developer's shell leaks into the tests (e.g. a Redis broker).
for _key in [k for k in os.environ if k.startswith("APP_")]:
    del os.environ[_key]

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from fastapi_starter.config import Settings, get_settings  # noqa: E402
from fastapi_starter.db import Base, create_engine, create_sessionmaker  # noqa: E402
from fastapi_starter.main import create_app  # noqa: E402

UPSTREAM = "https://upstream.test"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        environment="test",
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'test.db'}",
        upload_dir=tmp_path / "uploads",
        message_log=tmp_path / "messages.log",
        max_upload_bytes=1024,
        broker_url="",
        external_api_url=UPSTREAM,
    )


async def _create_schema(url: str) -> None:
    engine = create_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


@pytest.fixture
def schema(settings: Settings) -> None:
    asyncio.run(_create_schema(settings.database_url))


def upstream_handler(request: httpx2.Request) -> httpx2.Response:
    """Fake JSONPlaceholder: /todos/1 exists, /todos/500 errors, /todos/503 is down."""
    if request.url.path == "/todos/1":
        return httpx2.Response(200, json={"id": 1, "title": "delectus aut autem"})
    if request.url.path == "/todos/500":
        return httpx2.Response(500, text="boom")
    if request.url.path == "/todos/503":
        raise httpx2.ConnectError("connection refused", request=request)
    if request.url.path == "/todos/2":
        return httpx2.Response(200, text="<html>not json</html>")
    return httpx2.Response(404, json={})


@pytest.fixture
def http_client() -> httpx2.AsyncClient:
    return httpx2.AsyncClient(base_url=UPSTREAM, transport=httpx2.MockTransport(upstream_handler))


@pytest.fixture
def client(
    settings: Settings, schema: None, http_client: httpx2.AsyncClient
) -> Iterator[TestClient]:
    app = create_app(settings, http_client=http_client)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def seeded(client: TestClient) -> TestClient:
    for name in ("Mozzarella", "Tomato sauce", "Ham", "Basil"):
        client.post("/api/toppings", json={"name": name})
    client.post("/api/chefs", json={"name": "Mario"})
    return client


@pytest.fixture
async def session(settings: Settings) -> AsyncIterator[AsyncSession]:
    await _create_schema(settings.database_url)
    engine = create_engine(settings.database_url)
    async with create_sessionmaker(engine)() as s:
        yield s
    await engine.dispose()


@pytest.fixture
def cli_env(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> Iterator[Settings]:
    """Point the process-wide settings (used by the CLI) at the temp database."""
    monkeypatch.setenv("APP_DATABASE_URL", settings.database_url)
    monkeypatch.setenv("APP_LOG_LEVEL", "WARNING")
    get_settings.cache_clear()
    yield settings
    get_settings.cache_clear()
