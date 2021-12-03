import aiofiles
import os

from typing import List
from collections import namedtuple

from fastapi import (HTTPException, APIRouter, Response,
    Depends, BackgroundTasks, File, UploadFile, Body,
    Request, WebSocket, status)
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, HTMLResponse
from tortoise.contrib.fastapi import HTTPNotFoundError
from tortoise.exceptions import OperationalError, DoesNotExist
from celery.result import AsyncResult

from models import Pizza, Topping, Chef, populate_db
from schemas import Pizza_Pydantic, PizzaIn_Pydantic, Topping_Pydantic
from services import write_message, save_static_file
from config import ALLOWED_UPLOAD_TYPES, STATIC_DIR
from tasks import create_task

Item = namedtuple('Item', 'label qty')

router = APIRouter()
templates = Jinja2Templates(directory = '../templates')

@router.get('/', response_model = List[Pizza_Pydantic])
async def all_pizzas():
    return await Pizza.all().prefetch_related('toppings', 'chef')

@router.get('/task')
async def long_running_task(message: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(write_message, message)
    return {'message': 'Message is added.'}

@router.post('/task')
async def run_long_task(payload = Body(...)):
    task_type = payload['type']
    task = create_task.delay(int(task_type))
    return JSONResponse({'task_id': task.id})

@router.get('/template')
async def simple_template(request: Request):
    context = {
        'request': request,
        'items': [
            Item(label = 'Eggs', qty = 12),
            Item(label = 'Milk', qty = 1),
            Item(label = 'Bread', qty = 1)
        ],
        'text': 42
    }
    return templates.TemplateResponse('page.html', context)

@router.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")

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

@router.post("/uploadfile/")
async def create_upload_file(response: Response, file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_UPLOAD_TYPES:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'error': 'This file extension is not allowed.'}
    await save_static_file(file)
    return {'message': 'OK'}
