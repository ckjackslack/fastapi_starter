"""Pure-ASGI middleware adding ``X-Request-ID`` and ``X-Process-Time`` to every HTTP response.

An incoming ``X-Request-ID`` (e.g. from a proxy) is reused if it looks sane, otherwise a new
one is generated. The id is also put on ``scope["state"]["request_id"]`` for handlers/logs.
"""

from __future__ import annotations

import logging
import re
import time
import uuid

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

log = logging.getLogger("fastapi_starter.access")

REQUEST_ID_HEADER = "x-request-id"
_VALID_ID = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


def pick_request_id(incoming: str | None) -> str:
    if incoming and _VALID_ID.match(incoming):
        return incoming
    return uuid.uuid4().hex


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        incoming = None
        for key, value in scope.get("headers", []):
            if key == REQUEST_ID_HEADER.encode():
                incoming = value.decode("latin-1")
                break
        request_id = pick_request_id(incoming)
        scope.setdefault("state", {})["request_id"] = request_id
        start = time.perf_counter()

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                elapsed_ms = (time.perf_counter() - start) * 1000
                headers = MutableHeaders(scope=message)
                headers["X-Request-ID"] = request_id
                headers["X-Process-Time"] = f"{elapsed_ms:.2f}ms"
                log.info(
                    "%s %s -> %s (%.1fms) [%s]",
                    scope["method"],
                    scope["path"],
                    message["status"],
                    elapsed_ms,
                    request_id,
                )
            await send(message)

        await self.app(scope, receive, send_wrapper)
