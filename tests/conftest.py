from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.app import create_app
from app.core.database import Base, get_db
from app.core.openai import get_openai_client


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession]:
    session = AsyncSession(bind=test_engine, expire_on_commit=False)
    try:
        yield session
    finally:
        await session.close()


@pytest_asyncio.fixture(autouse=True)
async def clean_db(test_engine) -> AsyncGenerator[None]:
    yield
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest_asyncio.fixture
async def app(db_session) -> FastAPI:
    application = create_app()

    async def _override_get_db() -> AsyncGenerator[AsyncSession]:
        yield db_session

    application.dependency_overrides[get_db] = _override_get_db
    return application


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as _client:
        yield _client


@pytest_asyncio.fixture
async def mock_openai() -> AsyncMock:
    return AsyncMock(spec=AsyncOpenAI)


@pytest_asyncio.fixture
async def app_with_openai(app: FastAPI, mock_openai: AsyncMock) -> FastAPI:
    async def _override_openai() -> AsyncGenerator[AsyncOpenAI]:
        yield mock_openai

    app.dependency_overrides[get_openai_client] = _override_openai
    return app


@pytest_asyncio.fixture
async def client_with_openai(app_with_openai: FastAPI) -> AsyncGenerator[AsyncClient]:
    transport = ASGITransport(app=app_with_openai)
    async with AsyncClient(transport=transport, base_url="http://test") as _client:
        yield _client
