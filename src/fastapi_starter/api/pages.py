"""Server-rendered page (Jinja2) and a WebSocket echo, as in the original demo."""

from pathlib import Path

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .. import crud
from .deps import SessionDep

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)

router = APIRouter(include_in_schema=False)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, session: SessionDep) -> HTMLResponse:
    pizzas, total = await crud.list_pizzas(session, limit=20)
    return templates.TemplateResponse(
        request,
        "index.html",
        {"pizzas": pizzas, "total": total, "app_name": request.app.title},
    )


@router.websocket("/ws/echo")
async def echo(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            text = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {text}")
    except WebSocketDisconnect:
        pass
