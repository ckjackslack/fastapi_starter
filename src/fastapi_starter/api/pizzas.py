"""REST CRUD for pizzas, chefs and toppings."""

from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from .. import crud
from ..schemas import (
    ChefCreate,
    ChefRead,
    Page,
    PizzaCreate,
    PizzaRead,
    PizzaUpdate,
    ToppingCreate,
    ToppingRead,
)
from .deps import SessionDep

router = APIRouter(tags=["pizzas"])


@router.get("/pizzas")
async def list_pizzas(
    session: SessionDep,
    response: Response,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    topping: Annotated[str | None, Query(description="Only pizzas with this topping.")] = None,
    chef: Annotated[str | None, Query(description="Only pizzas by this chef.")] = None,
    q: Annotated[str | None, Query(description="Substring search in the pizza name.")] = None,
) -> Page[PizzaRead]:
    items, total = await crud.list_pizzas(
        session, limit=limit, offset=offset, topping=topping, chef=chef, search=q
    )
    response.headers["X-Total-Count"] = str(total)
    return Page[PizzaRead](
        items=[PizzaRead.model_validate(p) for p in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/pizzas/{pizza_id}")
async def get_pizza(pizza_id: int, session: SessionDep) -> PizzaRead:
    return PizzaRead.model_validate(await crud.get_pizza(session, pizza_id))


@router.post("/pizzas", status_code=status.HTTP_201_CREATED)
async def create_pizza(data: PizzaCreate, session: SessionDep) -> PizzaRead:
    return PizzaRead.model_validate(await crud.create_pizza(session, data))


@router.patch("/pizzas/{pizza_id}")
async def update_pizza(pizza_id: int, data: PizzaUpdate, session: SessionDep) -> PizzaRead:
    return PizzaRead.model_validate(await crud.update_pizza(session, pizza_id, data))


@router.delete("/pizzas/{pizza_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pizza(pizza_id: int, session: SessionDep) -> None:
    await crud.delete_pizza(session, pizza_id)


@router.get("/chefs", tags=["chefs"])
async def list_chefs(session: SessionDep) -> list[ChefRead]:
    return [ChefRead.model_validate(c) for c in await crud.list_chefs(session)]


@router.post("/chefs", tags=["chefs"], status_code=status.HTTP_201_CREATED)
async def create_chef(data: ChefCreate, session: SessionDep) -> ChefRead:
    return ChefRead.model_validate(await crud.create_chef(session, data.name))


@router.get("/toppings", tags=["toppings"])
async def list_toppings(session: SessionDep) -> list[ToppingRead]:
    return [ToppingRead.model_validate(t) for t in await crud.list_toppings(session)]


@router.post("/toppings", tags=["toppings"], status_code=status.HTTP_201_CREATED)
async def create_topping(data: ToppingCreate, session: SessionDep) -> ToppingRead:
    return ToppingRead.model_validate(await crud.create_topping(session, data.name))
