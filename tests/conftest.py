from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from contextlib import suppress
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from openai import AsyncOpenAI
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.app import create_app
from app.core.database import Base
from app.core.dependencies import get_db, get_openai_client
from app.core.errors import OpenAIException


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine("sqlite+aiosqlite://")

    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

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
    # Delete in reverse FK order to avoid constraint violations, then reset
    # SQLite autoincrement counters so each test starts with fresh IDs.
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
        with suppress(Exception):
            await conn.execute(text("DELETE FROM sqlite_sequence"))


@pytest_asyncio.fixture
async def app(db_session) -> FastAPI:
    application = create_app()

    async def _override_get_db() -> AsyncGenerator[AsyncSession]:
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

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


@pytest_asyncio.fixture
async def app_without_openai(app: FastAPI) -> FastAPI:
    async def _raise_openai():
        raise OpenAIException(detail="OpenAI client is not configured")

    app.dependency_overrides[get_openai_client] = _raise_openai
    return app


@pytest_asyncio.fixture
async def client_without_openai(app_without_openai: FastAPI) -> AsyncGenerator[AsyncClient]:
    transport = ASGITransport(app=app_without_openai)
    async with AsyncClient(transport=transport, base_url="http://test") as _client:
        yield _client


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


async def create_agent(client: AsyncClient) -> int:
    resp = await client.post("/api/v1/agents/", json={"name": "Test Agent"})
    return resp.json()["id"]


async def create_agent_and_session(client: AsyncClient) -> tuple[int, int]:
    agent_id = await create_agent(client)
    resp = await client.post("/api/v1/sessions/", json={"agent_id": agent_id})
    return agent_id, resp.json()["id"]


def mock_chat_completion(mock_openai: AsyncMock, response_text: str = "Hello back") -> None:
    mock_choice = MagicMock()
    mock_choice.message.content = response_text
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    mock_openai.chat.completions.create = AsyncMock(return_value=mock_completion)


@pytest_asyncio.fixture(autouse=True)
async def mock_aiofiles():
    with patch("aiofiles.open") as mock_open:
        mock_cm = AsyncMock()
        mock_file = AsyncMock()
        mock_cm.__aenter__.return_value = mock_file
        mock_open.return_value = mock_cm
        yield
