"""Service layer against a real (temporary) SQLite database."""

from __future__ import annotations

from datetime import UTC

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_starter import crud
from fastapi_starter.errors import ConflictError, InvalidReferenceError, NotFoundError
from fastapi_starter.models import Chef
from fastapi_starter.schemas import PizzaCreate, PizzaUpdate
from fastapi_starter.seed import PIZZAS, seed_demo_data

pytestmark = pytest.mark.anyio


async def test_seed_is_idempotent(session: AsyncSession) -> None:
    first = await seed_demo_data(session)
    assert first.pizzas == len(PIZZAS) and first.total > 0
    second = await seed_demo_data(session)
    assert second.total == 0
    _, total = await crud.list_pizzas(session)
    assert total == len(PIZZAS)


async def test_list_filters_and_pagination(session: AsyncSession) -> None:
    await seed_demo_data(session)

    items, total = await crud.list_pizzas(session, topping="  PINEAPPLE ")
    assert [p.name for p in items] == ["Hawaiian"] and total == 1

    items, _ = await crud.list_pizzas(session, chef="mario")
    assert [p.name for p in items] == ["Margherita"]

    items, total = await crud.list_pizzas(session, search="pep")
    assert [p.name for p in items] == ["Pepperoni"] and total == 1

    items, total = await crud.list_pizzas(session, search="%")  # wildcard is escaped
    assert items == [] and total == 0

    items, total = await crud.list_pizzas(session, limit=2, offset=1)
    assert len(items) == 2 and total == len(PIZZAS)
    assert items[0].name == "Hawaiian"


async def test_create_pizza_resolves_toppings_and_chef(session: AsyncSession) -> None:
    await seed_demo_data(session)
    pizza = await crud.create_pizza(
        session, PizzaCreate(name="veggie", chef_id=1, toppings=["basil", "TOMATO SAUCE"])
    )
    assert pizza.name == "Veggie"
    assert pizza.chef is not None and pizza.chef.name == "Mario"
    assert [t.name for t in pizza.toppings] == ["Basil", "Tomato sauce"]
    assert pizza.created_at.tzinfo is not None

    reloaded = await crud.get_pizza(session, pizza.id)
    assert reloaded.created_at.tzinfo == UTC


async def test_create_pizza_errors(session: AsyncSession) -> None:
    await seed_demo_data(session)
    with pytest.raises(InvalidReferenceError, match="Anchovy"):
        await crud.create_pizza(session, PizzaCreate(name="Fishy", toppings=["anchovy", "ham"]))
    with pytest.raises(InvalidReferenceError, match="Chef 99"):
        await crud.create_pizza(session, PizzaCreate(name="Ghost", chef_id=99))
    with pytest.raises(ConflictError):
        await crud.create_pizza(session, PizzaCreate(name="margherita"))
    # the session is still usable after the rolled back conflict
    _, total = await crud.list_pizzas(session)
    assert total == len(PIZZAS)


async def test_update_and_delete(session: AsyncSession) -> None:
    await seed_demo_data(session)
    pizza = await crud.update_pizza(
        session, 1, PizzaUpdate(name="margherita deluxe", toppings=["basil"])
    )
    assert pizza.name == "Margherita deluxe"
    assert [t.name for t in pizza.toppings] == ["Basil"]
    assert pizza.chef is not None  # untouched

    pizza = await crud.update_pizza(session, 1, PizzaUpdate.model_validate({"chef_id": None}))
    assert pizza.chef is None

    with pytest.raises(ConflictError):
        await crud.update_pizza(session, 1, PizzaUpdate(name="Hawaiian"))

    await crud.delete_pizza(session, 1)
    with pytest.raises(NotFoundError):
        await crud.get_pizza(session, 1)
    with pytest.raises(NotFoundError):
        await crud.delete_pizza(session, 1)


async def test_deleting_chef_keeps_pizza(session: AsyncSession) -> None:
    await seed_demo_data(session)
    chef = await session.get(Chef, 1)
    await session.delete(chef)
    await session.commit()
    session.expire_all()
    pizza = await crud.get_pizza(session, 1)
    assert pizza.chef is None  # ON DELETE SET NULL (foreign keys enabled on SQLite)


async def test_chef_and_topping_conflicts(session: AsyncSession) -> None:
    await crud.create_chef(session, "Mario")
    with pytest.raises(ConflictError):
        await crud.create_chef(session, "Mario")
    await crud.create_topping(session, "Ham")
    with pytest.raises(ConflictError):
        await crud.create_topping(session, "Ham")
    assert [c.name for c in await crud.list_chefs(session)] == ["Mario"]
    assert [t.name for t in await crud.list_toppings(session)] == ["Ham"]
