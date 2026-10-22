"""Taskiq broker and background jobs.

* ``APP_BROKER_URL`` empty (default): an in-process ``InMemoryBroker``. Jobs run inside the
  web process; perfect for development and tests, no Redis needed.
* ``APP_BROKER_URL=redis://...``: a Redis stream broker + Redis result backend. Run the
  worker separately with ``fastapi-starter worker`` (or ``taskiq worker
  fastapi_starter.worker:broker``).
"""

from __future__ import annotations

import asyncio
import logging

from taskiq import AsyncBroker, InMemoryBroker

from .config import Settings, get_settings

log = logging.getLogger(__name__)


def make_broker(settings: Settings) -> AsyncBroker:
    if settings.uses_redis_broker:
        try:
            from taskiq_redis import RedisAsyncResultBackend, RedisStreamBroker
        except ImportError as exc:  # pragma: no cover - depends on installed extras
            raise RuntimeError(
                "APP_BROKER_URL points to Redis but taskiq-redis is not installed. "
                "Install the 'redis' extra: pip install 'fastapi-starter[redis]'."
            ) from exc
        return RedisStreamBroker(settings.broker_url).with_result_backend(
            RedisAsyncResultBackend(settings.broker_url, result_ex_time=3600)
        )
    if settings.broker_url:
        raise RuntimeError(f"Unsupported APP_BROKER_URL scheme: {settings.broker_url!r}")
    return InMemoryBroker()


broker: AsyncBroker = make_broker(get_settings())


def bake_message(name: str, seconds: float) -> str:
    return f"{name} is ready after {seconds:g}s in the oven."


@broker.task(task_name="bake_pizza")
async def bake_pizza(name: str, seconds: float = 1.0) -> str:
    """Pretend to bake a pizza: the 'long running job' of the starter."""
    log.info("Baking %s for %.1fs", name, seconds)
    await asyncio.sleep(seconds)
    return bake_message(name, seconds)
