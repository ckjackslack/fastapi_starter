"""Application factory. ``fastapi_starter.main:app`` is the ASGI entry point."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from taskiq import AsyncBroker, InMemoryBroker

from . import __version__
from .api import api_router, pages
from .config import Settings, get_settings
from .db import create_engine, create_sessionmaker
from .errors import AppError
from .middleware import RequestContextMiddleware
from .services.external import build_client

STATIC_DIR = Path(__file__).resolve().parent / "static"
log = logging.getLogger(__name__)


def create_app(
    settings: Settings | None = None,
    *,
    http_client: httpx.AsyncClient | None = None,
    broker: AsyncBroker | None = None,
) -> FastAPI:
    """Build the app. Tests pass their own settings, a mocked HTTP client and/or a broker."""
    settings = settings or get_settings()
    if broker is None:
        from .worker import broker as default_broker

        broker = default_broker

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_engine(settings.database_url, echo=settings.database_echo)
        app.state.engine = engine
        app.state.sessionmaker = create_sessionmaker(engine)
        app.state.http_client = http_client or build_client(
            settings.external_api_url, settings.external_api_timeout
        )
        if not broker.is_worker_process:
            await broker.startup()
        log.info("%s %s started (%s)", settings.app_name, __version__, settings.environment)
        try:
            yield
        finally:
            if not broker.is_worker_process:
                if isinstance(broker, InMemoryBroker):
                    await broker.wait_all()  # let in-process jobs finish gracefully
                await broker.shutdown()
            if http_client is None:
                await app.state.http_client.aclose()
            await engine.dispose()

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        debug=settings.debug,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.broker = broker

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time", "X-Total-Count"],
    )
    app.add_middleware(RequestContextMiddleware)

    @app.exception_handler(AppError)
    async def _app_error(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

    app.include_router(api_router)
    app.include_router(pages.router)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app


def __getattr__(name: str) -> FastAPI:
    # Lazily build the default app so importing this module (e.g. in tests) has no side effects.
    if name == "app":
        global app
        app = create_app()
        return app
    raise AttributeError(name)
