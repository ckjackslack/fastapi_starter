"""Pure logic: name normalization, schemas, config parsing, broker selection, filenames."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from fastapi_starter.config import Settings
from fastapi_starter.errors import NotFoundError, UnsupportedMediaError
from fastapi_starter.middleware import pick_request_id
from fastapi_starter.schemas import PizzaCreate, PizzaUpdate, normalize_name, unique_names
from fastapi_starter.services.storage import (
    check_content_type,
    resolve_stored,
    safe_filename,
    unique_path,
)
from fastapi_starter.worker import bake_message, make_broker


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("  tomato   sauce ", "Tomato sauce"),
        ("ham", "Ham"),
        ("BBQ chicken", "BBQ chicken"),
        ("x", "X"),
    ],
)
def test_normalize_name(raw: str, expected: str) -> None:
    assert normalize_name(raw) == expected


def test_unique_names_dedupes_case_insensitively_keeping_order() -> None:
    assert unique_names(["ham", "Basil", "HAM", " basil "]) == ["Ham", "Basil"]


def test_pizza_create_normalizes() -> None:
    pizza = PizzaCreate(name="  quattro  formaggi ", toppings=["mozzarella", "Mozzarella"])
    assert pizza.name == "Quattro formaggi"
    assert pizza.toppings == ["Mozzarella"]


@pytest.mark.parametrize("name", ["", "   ", "x" * 129])
def test_pizza_create_rejects_bad_names(name: str) -> None:
    with pytest.raises(ValidationError):
        PizzaCreate(name=name)


def test_pizza_update_tracks_sent_fields_only() -> None:
    update = PizzaUpdate.model_validate({"chef_id": None})
    assert update.model_dump(exclude_unset=True) == {"chef_id": None}


def test_settings_parse_comma_separated_and_json_lists(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_CORS_ORIGINS", "http://a.test, http://b.test")
    monkeypatch.setenv("APP_ALLOWED_UPLOAD_TYPES", '["text/plain"]')
    s = Settings(_env_file=None)
    assert s.cors_origins == ["http://a.test", "http://b.test"]
    assert s.allowed_upload_types == ["text/plain"]


def test_settings_defaults_need_no_environment() -> None:
    s = Settings(_env_file=None)
    assert s.database_url.startswith("sqlite+aiosqlite://")
    assert not s.uses_redis_broker


def test_make_broker_in_memory_by_default() -> None:
    from taskiq import InMemoryBroker

    assert isinstance(make_broker(Settings(_env_file=None)), InMemoryBroker)


def test_make_broker_rejects_unknown_scheme() -> None:
    with pytest.raises(RuntimeError, match="Unsupported"):
        make_broker(Settings(_env_file=None, broker_url="amqp://guest@localhost//"))


def test_make_broker_redis_when_configured() -> None:
    pytest.importorskip("taskiq_redis")
    broker = make_broker(Settings(_env_file=None, broker_url="redis://localhost:6379/0"))
    assert type(broker).__name__ == "RedisStreamBroker"  # constructed lazily, no connection


def test_bake_message() -> None:
    assert bake_message("Margherita", 1.5) == "Margherita is ready after 1.5s in the oven."


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("../../etc/passwd", "passwd"),
        ("..\\..\\boot.ini", "boot.ini"),
        ("Financial Sample (1).xlsx", "Financial_Sample_1_.xlsx"),
        ("zażółć.pdf", "zazoc.pdf"),
        ("", "upload"),
        (None, "upload"),
        ("...", "upload"),
    ],
)
def test_safe_filename(raw: str | None, expected: str) -> None:
    assert safe_filename(raw) == expected


def test_unique_path_adds_counter(tmp_path: Path) -> None:
    (tmp_path / "a.pdf").write_bytes(b"1")
    (tmp_path / "a-1.pdf").write_bytes(b"2")
    assert unique_path(tmp_path, "a.pdf").name == "a-2.pdf"
    assert unique_path(tmp_path, "b.pdf").name == "b.pdf"


def test_check_content_type() -> None:
    check_content_type("application/pdf", ["application/pdf"])
    check_content_type("text/csv; charset=utf-8", ["text/csv"])
    with pytest.raises(UnsupportedMediaError):
        check_content_type("image/png", ["application/pdf"])
    with pytest.raises(UnsupportedMediaError):
        check_content_type(None, ["application/pdf"])


def test_resolve_stored_refuses_traversal(tmp_path: Path) -> None:
    (tmp_path / "ok.pdf").write_bytes(b"x")
    assert resolve_stored(tmp_path, "ok.pdf") == tmp_path / "ok.pdf"
    for bad in ("../ok.pdf", "missing.pdf", ".hidden"):
        with pytest.raises(NotFoundError):
            resolve_stored(tmp_path, bad)


def test_pick_request_id() -> None:
    assert pick_request_id("abc-123") == "abc-123"
    generated = pick_request_id("bad id with spaces")
    assert len(generated) == 32 and generated != "bad id with spaces"
    assert len(pick_request_id(None)) == 32
