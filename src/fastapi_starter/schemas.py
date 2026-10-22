"""Pydantic v2 request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints

from .models import NAME_LENGTH


def normalize_name(value: str) -> str:
    """Canonical form for names: trimmed, inner whitespace collapsed, first letter upper.

    >>> normalize_name("  tomato   sauce ")
    'Tomato sauce'
    """
    collapsed = " ".join(value.split())
    return collapsed[:1].upper() + collapsed[1:]


def unique_names(values: list[str]) -> list[str]:
    """Normalize and de-duplicate (case-insensitively), keeping first-seen order."""
    seen: dict[str, str] = {}
    for value in values:
        name = normalize_name(value)
        seen.setdefault(name.casefold(), name)
    return list(seen.values())


Name = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=NAME_LENGTH),
    AfterValidator(normalize_name),
]
NameList = Annotated[list[Name], AfterValidator(unique_names)]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- chefs & toppings -------------------------------------------------------------


class ChefCreate(BaseModel):
    name: Name


class ChefRead(ORMModel):
    id: int
    name: str


class ToppingCreate(BaseModel):
    name: Name


class ToppingRead(ORMModel):
    id: int
    name: str


# --- pizzas ---------------------------------------------------------------------------


class PizzaCreate(BaseModel):
    name: Name
    chef_id: int | None = None
    toppings: NameList = Field(default_factory=list, description="Topping names.")


class PizzaUpdate(BaseModel):
    """Partial update: only the fields that are sent are changed."""

    name: Name | None = None
    chef_id: int | None = None
    toppings: NameList | None = None


class PizzaRead(ORMModel):
    id: int
    name: str
    chef: ChefRead | None
    toppings: list[ToppingRead]
    created_at: datetime


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int


# --- tasks ------------------------------------------------------------------------------


class MessageIn(BaseModel):
    message: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class BakeRequest(BaseModel):
    seconds: float = Field(default=1.0, ge=0, le=60, description="Simulated baking time.")


class TaskQueued(BaseModel):
    task_id: str


class TaskStatus(BaseModel):
    task_id: str
    status: Literal["pending", "success", "failure"]
    result: object | None = None
    error: str | None = None


# --- files / misc ---------------------------------------------------------------------


class StoredFile(BaseModel):
    name: str
    size: int
    content_type: str | None = None


class SheetPreview(BaseModel):
    sheet: str
    header: list[object]
    rows: list[list[object]]
    total_rows: int
    total_columns: int


class Health(BaseModel):
    status: Literal["ok", "degraded"]
    version: str
    database: Literal["ok", "unavailable"]
