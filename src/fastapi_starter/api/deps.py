"""FastAPI dependencies. Everything comes from ``app.state`` so tests can swap it out."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

import httpx2
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from taskiq import AsyncBroker

from ..config import Settings


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.sessionmaker() as session:
        yield session


def get_http_client(request: Request) -> httpx2.AsyncClient:
    return request.app.state.http_client


def get_broker(request: Request) -> AsyncBroker:
    return request.app.state.broker


SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]
HttpClientDep = Annotated[httpx2.AsyncClient, Depends(get_http_client)]
BrokerDep = Annotated[AsyncBroker, Depends(get_broker)]
