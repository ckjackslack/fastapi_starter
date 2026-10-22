"""Health check and the outgoing-HTTP demo."""

from typing import Annotated, Any

from fastapi import APIRouter, Path, Request, Response

from .. import __version__
from ..db import ping
from ..schemas import Health
from ..services.external import fetch_json
from .deps import HttpClientDep

router = APIRouter()


@router.get("/healthz", tags=["meta"], responses={503: {"model": Health}})
async def health(request: Request, response: Response) -> Health:
    """Liveness + database readiness. Answers 503 when the database is unreachable."""
    db_ok = await ping(request.app.state.engine)
    body = Health(
        status="ok" if db_ok else "degraded",
        version=__version__,
        database="ok" if db_ok else "unavailable",
    )
    if not db_ok:
        response.status_code = 503
    return body


@router.get("/external/todos/{todo_id}", tags=["external"])
async def external_todo(
    todo_id: Annotated[int, Path(ge=1)], client: HttpClientDep
) -> dict[str, Any]:
    """Fetch a todo from the configured upstream (JSONPlaceholder by default)."""
    return await fetch_json(client, f"/todos/{todo_id}")
