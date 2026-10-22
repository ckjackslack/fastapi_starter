"""Database operations for the pizza domain. Pure SQLAlchemy, no HTTP concerns."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .errors import ConflictError, InvalidReferenceError, NotFoundError
from .models import Chef, Pizza, Topping
from .schemas import PizzaCreate, PizzaUpdate

# --- chefs & toppings -------------------------------------------------------------------


async def list_chefs(session: AsyncSession) -> Sequence[Chef]:
    return (await session.scalars(select(Chef).order_by(Chef.name))).all()


async def create_chef(session: AsyncSession, name: str) -> Chef:
    chef = Chef(name=name)
    session.add(chef)
    await _commit_unique(session, f"Chef {name!r} already exists.")
    return chef


async def list_toppings(session: AsyncSession) -> Sequence[Topping]:
    return (await session.scalars(select(Topping).order_by(Topping.name))).all()


async def create_topping(session: AsyncSession, name: str) -> Topping:
    topping = Topping(name=name)
    session.add(topping)
    await _commit_unique(session, f"Topping {name!r} already exists.")
    return topping


async def resolve_toppings(session: AsyncSession, names: Sequence[str]) -> list[Topping]:
    """Look up toppings by (case-insensitive) name, sorted by name; fail on unknown names."""
    if not names:
        return []
    wanted = {name.casefold(): name for name in names}
    rows = await session.scalars(select(Topping).where(func.lower(Topping.name).in_(list(wanted))))
    found = {t.name.casefold(): t for t in rows}
    missing = [name for key, name in wanted.items() if key not in found]
    if missing:
        raise InvalidReferenceError(f"Unknown toppings: {', '.join(missing)}")
    return sorted((found[key] for key in wanted), key=lambda t: t.name)


async def _resolve_chef(session: AsyncSession, chef_id: int | None) -> Chef | None:
    if chef_id is None:
        return None
    chef = await session.get(Chef, chef_id)
    if chef is None:
        raise InvalidReferenceError(f"Chef {chef_id} does not exist.")
    return chef


# --- pizzas --------------------------------------------------------------------------------


async def list_pizzas(
    session: AsyncSession,
    *,
    limit: int = 50,
    offset: int = 0,
    topping: str | None = None,
    chef: str | None = None,
    search: str | None = None,
) -> tuple[Sequence[Pizza], int]:
    """Return one page of pizzas plus the total number matching the filters."""
    query = select(Pizza)
    if topping:
        query = query.where(
            Pizza.toppings.any(func.lower(Topping.name) == topping.strip().casefold())
        )
    if chef:
        query = query.where(Pizza.chef.has(func.lower(Chef.name) == chef.strip().casefold()))
    if search:
        query = query.where(Pizza.name.icontains(search.strip(), autoescape=True))

    total = await session.scalar(select(func.count()).select_from(query.subquery()))
    rows = await session.scalars(query.order_by(Pizza.id).limit(limit).offset(offset))
    return rows.all(), total or 0


async def get_pizza(session: AsyncSession, pizza_id: int) -> Pizza:
    pizza = await session.get(Pizza, pizza_id)
    if pizza is None:
        raise NotFoundError(f"Pizza {pizza_id} does not exist.")
    return pizza


async def create_pizza(session: AsyncSession, data: PizzaCreate) -> Pizza:
    pizza = Pizza(
        name=data.name,
        chef=await _resolve_chef(session, data.chef_id),
        toppings=await resolve_toppings(session, data.toppings),
    )
    session.add(pizza)
    await _commit_unique(session, f"Pizza {data.name!r} already exists.")
    return pizza


async def update_pizza(session: AsyncSession, pizza_id: int, data: PizzaUpdate) -> Pizza:
    pizza = await get_pizza(session, pizza_id)
    changes = data.model_dump(exclude_unset=True)
    if "name" in changes and data.name is not None:
        pizza.name = data.name
    if "chef_id" in changes:
        pizza.chef = await _resolve_chef(session, data.chef_id)
    if "toppings" in changes:
        pizza.toppings = await resolve_toppings(session, data.toppings or [])
    await _commit_unique(session, f"Pizza {pizza.name!r} already exists.")
    return pizza


async def delete_pizza(session: AsyncSession, pizza_id: int) -> None:
    pizza = await get_pizza(session, pizza_id)
    await session.delete(pizza)
    await session.commit()


async def _commit_unique(session: AsyncSession, message: str) -> None:
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ConflictError(message) from exc
