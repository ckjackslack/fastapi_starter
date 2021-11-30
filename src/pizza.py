from typing import List

from fastapi import (HTTPException, APIRouter, Response,
    Depends, status)
from tortoise.contrib.fastapi import HTTPNotFoundError
from tortoise.exceptions import OperationalError, DoesNotExist

from models import Pizza, Topping, Chef, populate_db
from schemas import Pizza_Pydantic, PizzaIn_Pydantic, Topping_Pydantic

router = APIRouter()

@router.get('/', response_model = List[Pizza_Pydantic])
async def all_pizzas():
    return await Pizza.all().prefetch_related('toppings', 'chef')

@router.get('/{pizza_id}')
async def single_pizza(pizza_id: int) -> Pizza_Pydantic:
    return await Pizza_Pydantic.from_queryset_single(Pizza.get(id = pizza_id))

@router.post('/')
async def new_pizza(pizza: PizzaIn_Pydantic, toppings: List[Topping_Pydantic],
    response: Response):
    try:
        toppings = await Topping.filter(
            name__in = {t.name.capitalize() for t in toppings})
        obj = await Pizza.create(name = pizza.name)
        await obj.toppings.add(*toppings)
        response.status_code = status.HTTP_201_CREATED
        return obj
    except OperationalError:
        response.status_code = status.HTTP_409_CONFLICT
        return {'error': 'Pizza with given name already exists.'}

@router.delete('/{pizza_id}')
async def delete_pizza(pizza_id: int, response: Response):
    deleted_count = await Pizza.filter(pk = pizza_id).delete()
    if not deleted_count:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'error': 'Pizza with given id does not exist.'}
    else:
        response.status_code = status.HTTP_204_NO_CONTENT