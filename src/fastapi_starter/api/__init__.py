"""HTTP routers. JSON endpoints live under ``/api``; the demo page and WebSocket at the root."""

from fastapi import APIRouter

from . import files, misc, pages, pizzas, tasks

api_router = APIRouter(prefix="/api")
api_router.include_router(pizzas.router)
api_router.include_router(tasks.router)
api_router.include_router(files.router)
api_router.include_router(misc.router)

__all__ = ["api_router", "pages"]
