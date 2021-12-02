import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise

from config import DB_CONNECTION_STRING
from models import populate_db
from pizza import router as PizzaRouter

log = logging.getLogger(__name__)

async def init_db(app: FastAPI) -> None:
    TORTOISE_ORM = {
        'connections': {
            'default': DB_CONNECTION_STRING\
                .format(filename = 'pizza'),
        },
        'apps': {
            'models': {
                'models': ['models'],
                'default_connection': 'default',
            },
        },
    }
    await Tortoise.init(config = TORTOISE_ORM)
    await Tortoise.generate_schemas()

    register_tortoise(
        app,
        config = TORTOISE_ORM,
        generate_schemas = True,
        add_exception_handlers = True,
    )
    await populate_db()

app = FastAPI()
app.include_router(PizzaRouter, prefix = '/pizza')
app.add_middleware(
    CORSMiddleware,
    allow_origins = '*',
    allow_credentials = True,
    allow_methods = ['*'],
    allow_headers = ['*'],
)

@app.on_event('startup')
async def startup_event():
    log.info('Initializing database.')
    await init_db(app)

@app.on_event('shutdown')
async def shutdown_event():
    await Tortoise.close_connections()
    log.info('Shutting down application.')