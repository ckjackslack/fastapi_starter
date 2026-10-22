"""Two flavours of background work.

* ``/tasks/messages``: FastAPI ``BackgroundTasks`` (runs after the response, same process).
  Good for small fire-and-forget jobs.
* ``/pizzas/{id}/bake`` + ``/tasks/{task_id}``: a Taskiq job with a result you can poll.
  In-process by default, a separate worker when ``APP_BROKER_URL`` points to Redis.
"""

from pathlib import Path
from typing import Annotated

import anyio
from fastapi import APIRouter, BackgroundTasks, Query, status

from .. import crud
from ..schemas import BakeRequest, MessageIn, TaskQueued, TaskStatus
from ..worker import bake_pizza
from .deps import BrokerDep, SessionDep, SettingsDep

router = APIRouter(tags=["tasks"])


async def append_message(path: Path, message: str) -> None:
    await anyio.Path(path.parent).mkdir(parents=True, exist_ok=True)
    async with await anyio.open_file(path, "a", encoding="utf-8") as fh:
        await fh.write(f"{message}\n")


async def tail_lines(path: Path, count: int) -> list[str]:
    apath = anyio.Path(path)
    if not await apath.exists():
        return []
    lines = (await apath.read_text(encoding="utf-8")).splitlines()
    return lines[-count:]


@router.post("/tasks/messages", status_code=status.HTTP_202_ACCEPTED)
async def queue_message(
    data: MessageIn, background: BackgroundTasks, settings: SettingsDep
) -> dict[str, str]:
    background.add_task(append_message, settings.message_log, data.message)
    return {"detail": "Message accepted."}


@router.get("/tasks/messages")
async def read_messages(
    settings: SettingsDep, last: Annotated[int, Query(ge=1, le=1000)] = 20
) -> list[str]:
    return await tail_lines(settings.message_log, last)


@router.post("/pizzas/{pizza_id}/bake", status_code=status.HTTP_202_ACCEPTED, tags=["pizzas"])
async def bake(pizza_id: int, session: SessionDep, data: BakeRequest | None = None) -> TaskQueued:
    pizza = await crud.get_pizza(session, pizza_id)
    job = await bake_pizza.kiq(pizza.name, (data or BakeRequest()).seconds)
    return TaskQueued(task_id=job.task_id)


@router.get("/tasks/{task_id}")
async def task_status(task_id: str, broker: BrokerDep) -> TaskStatus:
    """Unknown ids look the same as queued ones (``pending``): the backend can't tell them apart."""
    backend = broker.result_backend
    if not await backend.is_result_ready(task_id):
        return TaskStatus(task_id=task_id, status="pending")
    result = await backend.get_result(task_id)
    if result.is_err:
        return TaskStatus(task_id=task_id, status="failure", error=repr(result.error))
    return TaskStatus(task_id=task_id, status="success", result=result.return_value)
