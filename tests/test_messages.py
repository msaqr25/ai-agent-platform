from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from fastapi import status
from httpx import AsyncClient
from openai import OpenAIError


async def _create_agent_and_session(client: AsyncClient) -> tuple[int, int]:
    agent_resp = await client.post("/api/v1/agents/", json={"name": "Test Agent"})
    agent_id = agent_resp.json()["id"]
    session_resp = await client.post("/api/v1/sessions/", json={"agent_id": agent_id})
    session_id = session_resp.json()["id"]
    return agent_id, session_id


async def test_send_message(client_with_openai: AsyncClient, mock_openai: AsyncMock) -> None:
    _, session_id = await _create_agent_and_session(client_with_openai)

    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Hello back"
    mock_completion.choices = [mock_choice]
    mock_openai.chat.completions.create = AsyncMock(return_value=mock_completion)

    response = await client_with_openai.post(
        f"/api/v1/sessions/{session_id}/messages/",
        json={"content": "Hello"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["user_message"]["role"] == "user"
    assert data["user_message"]["content"] == "Hello"
    assert data["assistant_message"]["role"] == "assistant"
    assert data["assistant_message"]["content"] == "Hello back"
    assert data["user_message"]["audio_file"] is None
    assert data["assistant_message"]["audio_file"] is None


async def test_get_messages(client_with_openai: AsyncClient, mock_openai: AsyncMock) -> None:
    _, session_id = await _create_agent_and_session(client_with_openai)

    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Response"
    mock_completion.choices = [mock_choice]
    mock_openai.chat.completions.create = AsyncMock(return_value=mock_completion)

    await client_with_openai.post(f"/api/v1/sessions/{session_id}/messages/", json={"content": "First"})
    await client_with_openai.post(f"/api/v1/sessions/{session_id}/messages/", json={"content": "Second"})

    response = await client_with_openai.get(f"/api/v1/sessions/{session_id}/messages/")
    assert response.status_code == status.HTTP_200_OK
    messages = response.json()
    assert len(messages) == 4  # noqa: PLR2004


async def test_send_message_openai_error(client_with_openai: AsyncClient, mock_openai: AsyncMock) -> None:
    _, session_id = await _create_agent_and_session(client_with_openai)

    mock_openai.chat.completions.create = AsyncMock(side_effect=OpenAIError("API failure"))

    response = await client_with_openai.post(
        f"/api/v1/sessions/{session_id}/messages/",
        json={"content": "Hello"},
    )
    assert response.status_code == status.HTTP_502_BAD_GATEWAY
    data = response.json()
    assert data["code"] == "OPENAI_ERROR"


async def test_send_message_openai_error_does_not_persist(
    client_with_openai: AsyncClient, mock_openai: AsyncMock
) -> None:
    _, session_id = await _create_agent_and_session(client_with_openai)

    mock_openai.chat.completions.create = AsyncMock(side_effect=OpenAIError("API failure"))

    await client_with_openai.post(f"/api/v1/sessions/{session_id}/messages/", json={"content": "Hello"})

    response = await client_with_openai.get(f"/api/v1/sessions/{session_id}/messages/")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 0


async def test_get_messages_pagination(client_with_openai: AsyncClient, mock_openai: AsyncMock) -> None:
    _, session_id = await _create_agent_and_session(client_with_openai)

    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Response"
    mock_completion.choices = [mock_choice]
    mock_openai.chat.completions.create = AsyncMock(return_value=mock_completion)

    for i in range(5):
        await client_with_openai.post(f"/api/v1/sessions/{session_id}/messages/", json={"content": f"msg {i}"})

    response = await client_with_openai.get(f"/api/v1/sessions/{session_id}/messages/?skip=0&limit=2")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 2  # noqa: PLR2004


async def test_session_title_set_on_first_message(
    client_with_openai: AsyncClient,
    mock_openai: AsyncMock,
) -> None:
    _, session_id = await _create_agent_and_session(client_with_openai)

    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Assistant reply"
    mock_completion.choices = [mock_choice]
    mock_openai.chat.completions.create = AsyncMock(return_value=mock_completion)

    await client_with_openai.post(
        f"/api/v1/sessions/{session_id}/messages/",
        json={"content": "Hello, this is my first message in the session"},
    )

    session_resp = await client_with_openai.get(f"/api/v1/sessions/{session_id}")
    assert session_resp.status_code == status.HTTP_200_OK
    expected_title = "Hello, this is my first message in the session"[:60]
    assert session_resp.json()["title"] == expected_title
