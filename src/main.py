from fastapi import FastAPI, Response, status
from typing import List
from models import db
from schemas import Pizza, PizzaIn

app = FastAPI()

@app.get('/pizzas')
async def all_pizzas() -> List[Pizza]:
    return db

@app.post('/pizzas')
async def new_pizza(pizza: PizzaIn, response: Response):
    pizza_name = pizza.name.strip().lower()
    if pizza_name not in { p.name.lower() for p in db }:
        obj = Pizza(name = pizza.name, toppings = pizza.toppings)
        db.append(obj)
        response.status_code = status.HTTP_201_CREATED
        return obj
    else:
        response.status_code = status.HTTP_409_CONFLICT
        return {'error': 'Pizza with given name already exists.'}

@app.delete('/pizzas/{pizza_id}')
async def delete_pizza(pizza_id: int, response: Response):
    deleted = False
    for idx, pizza in enumerate(db):
        if pizza.id == pizza_id:
            del db[idx]
            deleted = True
            response.status_code = status.HTTP_204_NO_CONTENT
    if not deleted:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'error': 'Pizza with given id does not exist.'}