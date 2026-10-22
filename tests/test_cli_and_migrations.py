"""CLI commands and Alembic migrations (run against a temp SQLite file)."""

from __future__ import annotations

import io

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect

from fastapi_starter.cli import alembic_config, build_parser, main, run_migrations
from fastapi_starter.config import Settings
from fastapi_starter.db import Base


def sync_url(settings: Settings) -> str:
    return settings.database_url.replace("+aiosqlite", "")


def table_names(settings: Settings) -> set[str]:
    engine = create_engine(sync_url(settings))
    try:
        return set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def run(*argv: str) -> tuple[int, str]:
    out = io.StringIO()
    code = main(list(argv), out=out)
    return code, out.getvalue()


def test_help_lists_commands(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args(["--help"])
    assert exc.value.code == 0
    help_text = capsys.readouterr().out
    for cmd in ("serve", "migrate", "seed", "routes", "worker"):
        assert cmd in help_text


def test_missing_command_is_an_error(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code == 2


def test_migrate_then_seed(cli_env: Settings) -> None:
    code, out = run("migrate")
    assert code == 0 and "migrated to head" in out
    tables = table_names(cli_env)
    assert {"pizza", "chef", "topping", "pizza_topping", "alembic_version"} <= tables

    code, out = run("seed")
    assert code == 0 and out.startswith("Seeded ")
    code, out = run("seed")
    assert out.strip() == "Demo data already present."


def test_seed_without_schema_fails_cleanly(
    cli_env: Settings, capsys: pytest.CaptureFixture[str]
) -> None:
    code, _ = run("seed")
    assert code == 1
    assert "error:" in capsys.readouterr().err


def test_routes(cli_env: Settings) -> None:
    code, out = run("routes")
    assert code == 0
    lines = out.splitlines()
    assert any(line.split()[:2] == ["POST", "/api/pizzas"] for line in lines)
    assert any(line.split()[:2] == ["WS", "/ws/echo"] for line in lines)
    assert any(line.split()[:2] == ["GET", "/api/healthz"] for line in lines)


def test_worker_requires_redis_broker(
    cli_env: Settings, capsys: pytest.CaptureFixture[str]
) -> None:
    code, _ = run("worker")
    assert code == 2
    assert "in-process" in capsys.readouterr().err


def test_invalid_configuration(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from fastapi_starter.config import get_settings

    monkeypatch.setenv("APP_MAX_UPLOAD_BYTES", "lots")
    get_settings.cache_clear()
    try:
        code, _ = run("routes")
    finally:
        get_settings.cache_clear()
    assert code == 2
    assert "Invalid configuration" in capsys.readouterr().err


def test_migrations_match_models(settings: Settings) -> None:
    """Guard against model changes without a migration (alembic check, in a test)."""
    run_migrations(settings)
    engine = create_engine(sync_url(settings))
    try:
        with engine.connect() as conn:
            diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    finally:
        engine.dispose()
    assert diff == []


def test_downgrade_to_base(settings: Settings) -> None:
    run_migrations(settings)
    command.downgrade(alembic_config(settings), "base")
    assert table_names(settings) <= {"alembic_version"}
