"""``fastapi-starter`` command line: serve, migrate, seed, list routes, run the worker."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import shutil
import sys
from collections.abc import Sequence
from importlib.resources import files
from pathlib import Path
from typing import TextIO

from starlette.routing import BaseRoute

from . import __version__
from .config import Settings, get_settings


def alembic_config(settings: Settings):
    from alembic.config import Config

    cfg = Config()
    cfg.set_main_option("script_location", str(files("fastapi_starter") / "migrations"))
    cfg.attributes["database_url"] = settings.database_url
    return cfg


def run_migrations(settings: Settings, revision: str = "head") -> None:
    from alembic import command

    from .db import ensure_sqlite_dir

    ensure_sqlite_dir(settings.database_url)
    command.upgrade(alembic_config(settings), revision)


async def _seed(settings: Settings) -> int:
    from .db import create_engine, create_sessionmaker
    from .seed import seed_demo_data

    engine = create_engine(settings.database_url)
    try:
        async with create_sessionmaker(engine)() as session:
            report = await seed_demo_data(session)
    finally:
        await engine.dispose()
    return report.total


def iter_routes(app) -> list[tuple[str, BaseRoute]]:
    """(full path, original route) pairs, flattening included routers.

    FastAPI >= 0.140 keeps included routers lazily (``iter_route_contexts``); older releases
    copy every route into ``app.routes``. Support both.
    """
    try:
        from fastapi.routing import iter_route_contexts
    except ImportError:  # pragma: no cover - older FastAPI
        return [(getattr(r, "path", ""), r) for r in app.routes]
    return [(ctx.path or "", ctx.original_route) for ctx in iter_route_contexts(app.routes)]


def format_routes(app) -> list[str]:
    """One line per route: methods, path, endpoint name. Sorted by path."""
    from fastapi.routing import APIRoute, APIWebSocketRoute
    from starlette.routing import Mount, Route

    lines = []
    for path, route in iter_routes(app):
        if isinstance(route, APIRoute | Route):
            kind = ",".join(sorted((route.methods or set()) - {"HEAD"}))
        elif isinstance(route, APIWebSocketRoute):
            kind = "WS"
        elif isinstance(route, Mount):
            kind = "MOUNT"
        else:  # pragma: no cover
            continue
        lines.append((path, kind, f"{kind:<14} {path:<38} {route.name}"))
    return [line for *_, line in sorted(lines)]


# --- commands -------------------------------------------------------------------------


def cmd_serve(args: argparse.Namespace, settings: Settings, out: TextIO) -> int:
    import uvicorn

    if args.migrate:
        run_migrations(settings)
    if args.seed:
        asyncio.run(_seed(settings))
    uvicorn.run(
        "fastapi_starter.main:create_app",
        factory=True,
        host=args.host,
        port=args.port,
        reload=args.reload,
        reload_dirs=[str(Path(__file__).resolve().parent)] if args.reload else None,
        log_level=settings.log_level.lower(),
        proxy_headers=True,
    )
    return 0


def cmd_migrate(args: argparse.Namespace, settings: Settings, out: TextIO) -> int:
    run_migrations(settings, args.revision)
    print(f"Database at {settings.database_url} migrated to {args.revision}.", file=out)
    return 0


def cmd_seed(args: argparse.Namespace, settings: Settings, out: TextIO) -> int:
    added = asyncio.run(_seed(settings))
    print(f"Seeded {added} new rows." if added else "Demo data already present.", file=out)
    return 0


def cmd_routes(args: argparse.Namespace, settings: Settings, out: TextIO) -> int:
    from .main import create_app

    for line in format_routes(create_app(settings)):
        print(line, file=out)
    return 0


def cmd_worker(args: argparse.Namespace, settings: Settings, out: TextIO) -> int:
    if not settings.uses_redis_broker:
        print(
            "APP_BROKER_URL is not a redis:// URL: jobs already run in-process with the web "
            "app, there is nothing for a separate worker to consume.",
            file=sys.stderr,
        )
        return 2
    taskiq = shutil.which("taskiq")
    if taskiq is None:
        print("The 'taskiq' executable was not found on PATH.", file=sys.stderr)
        return 2
    argv = [taskiq, "worker", "fastapi_starter.worker:broker", *args.extra]
    os.execv(taskiq, argv)  # pragma: no cover - replaces the process
    return 0  # pragma: no cover


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fastapi-starter",
        description="Run and manage the FastAPI starter app. Configure via APP_* env vars or .env.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    serve = sub.add_parser("serve", help="run the web app with uvicorn")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--reload", action="store_true", help="auto-reload on code changes")
    serve.add_argument("--migrate", action="store_true", help="apply migrations first")
    serve.add_argument("--seed", action="store_true", help="insert demo data first")
    serve.set_defaults(func=cmd_serve)

    migrate = sub.add_parser("migrate", help="apply Alembic migrations")
    migrate.add_argument("revision", nargs="?", default="head")
    migrate.set_defaults(func=cmd_migrate)

    seed = sub.add_parser("seed", help="insert demo chefs, toppings and pizzas (idempotent)")
    seed.set_defaults(func=cmd_seed)

    routes = sub.add_parser("routes", help="list all HTTP/WebSocket routes")
    routes.set_defaults(func=cmd_routes)

    worker = sub.add_parser("worker", help="run the Taskiq worker (needs a redis:// broker)")
    worker.add_argument("extra", nargs=argparse.REMAINDER, help="extra args for taskiq worker")
    worker.set_defaults(func=cmd_worker)
    return parser


def main(argv: Sequence[str] | None = None, *, out: TextIO | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        settings = get_settings()
    except Exception as exc:  # pydantic ValidationError on bad env values
        print(f"Invalid configuration: {exc}", file=sys.stderr)
        return 2
    logging.basicConfig(
        level=settings.log_level.upper(), format="%(levelname)s %(name)s: %(message)s"
    )
    logging.getLogger("alembic.runtime.plugins").setLevel(logging.WARNING)
    try:
        return args.func(args, settings, out or sys.stdout)
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
