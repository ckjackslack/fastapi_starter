"""Outgoing HTTP calls with httpx2 (the maintained httpx successor; replaces aiohttp).

One ``httpx2.AsyncClient`` is created in the app lifespan and injected, so tests can pass a
client built on ``httpx2.MockTransport`` and never touch the network.
"""

from __future__ import annotations

from typing import Any

import httpx2

from ..errors import NotFoundError, UpstreamError


def build_client(base_url: str, timeout: float) -> httpx2.AsyncClient:
    return httpx2.AsyncClient(
        base_url=base_url,
        timeout=timeout,
        headers={"User-Agent": "fastapi-starter"},
        follow_redirects=True,
    )


async def fetch_json(client: httpx2.AsyncClient, path: str) -> Any:
    try:
        response = await client.get(path)
    except httpx2.HTTPError as exc:
        raise UpstreamError(f"Upstream request failed: {exc.__class__.__name__}") from exc
    if response.status_code == 404:
        raise NotFoundError(f"Upstream resource {path!r} not found.")
    if response.is_error:
        raise UpstreamError(f"Upstream answered {response.status_code}.")
    try:
        return response.json()
    except ValueError as exc:
        raise UpstreamError("Upstream did not return JSON.") from exc
