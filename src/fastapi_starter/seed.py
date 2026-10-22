"""Deterministic, idempotent demo data (the original seeded random toppings on every boot)."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Chef, Pizza, Topping

CHEFS = ("Mario", "Luigi", "Gordon Ramsay")
TOPPINGS = ("Pepperoni", "Ham", "Pineapple", "Mozzarella", "Tomato sauce", "Basil")
PIZZAS: dict[str, tuple[str, tuple[str, ...]]] = {
    "Margherita": ("Mario", ("Tomato sauce", "Mozzarella", "Basil")),
    "Hawaiian": ("Luigi", ("Tomato sauce", "Mozzarella", "Ham", "Pineapple")),
    "Pepperoni": ("Gordon Ramsay", ("Tomato sauce", "Mozzarella", "Pepperoni")),
}


@dataclass(frozen=True)
class SeedReport:
    chefs: int
    toppings: int
    pizzas: int

    @property
    def total(self) -> int:
        return self.chefs + self.toppings + self.pizzas


async def seed_demo_data(session: AsyncSession) -> SeedReport:
    """Insert demo chefs, toppings and pizzas that do not exist yet. Returns what was added."""
    chefs = {c.name: c for c in await session.scalars(select(Chef))}
    toppings = {t.name: t for t in await session.scalars(select(Topping))}
    pizza_names = set(await session.scalars(select(Pizza.name)))

    new_chefs = [Chef(name=n) for n in CHEFS if n not in chefs]
    new_toppings = [Topping(name=n) for n in TOPPINGS if n not in toppings]
    session.add_all([*new_chefs, *new_toppings])
    chefs.update((c.name, c) for c in new_chefs)
    toppings.update((t.name, t) for t in new_toppings)

    new_pizzas = [
        Pizza(name=name, chef=chefs[chef], toppings=[toppings[t] for t in tops])
        for name, (chef, tops) in PIZZAS.items()
        if name not in pizza_names
    ]
    session.add_all(new_pizzas)
    await session.commit()
    return SeedReport(len(new_chefs), len(new_toppings), len(new_pizzas))
