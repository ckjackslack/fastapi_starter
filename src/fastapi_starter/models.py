"""ORM models for the demo pizza domain: pizzas have one (optional) chef and many toppings."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base, UTCDateTime

NAME_LENGTH = 128


def utcnow() -> datetime:
    return datetime.now(UTC)


pizza_topping = Table(
    "pizza_topping",
    Base.metadata,
    Column("pizza_id", ForeignKey("pizza.id", ondelete="CASCADE"), primary_key=True),
    Column("topping_id", ForeignKey("topping.id", ondelete="CASCADE"), primary_key=True),
)


class Chef(Base):
    __tablename__ = "chef"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(NAME_LENGTH), unique=True)

    pizzas: Mapped[list[Pizza]] = relationship(back_populates="chef", lazy="raise")


class Topping(Base):
    __tablename__ = "topping"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(NAME_LENGTH), unique=True)


class Pizza(Base):
    __tablename__ = "pizza"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(NAME_LENGTH), unique=True)
    chef_id: Mapped[int | None] = mapped_column(
        ForeignKey("chef.id", ondelete="SET NULL"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)

    # selectin loading keeps async code free of implicit lazy loads.
    chef: Mapped[Chef | None] = relationship(back_populates="pizzas", lazy="selectin")
    toppings: Mapped[list[Topping]] = relationship(
        secondary=pizza_topping, lazy="selectin", order_by=Topping.name
    )
