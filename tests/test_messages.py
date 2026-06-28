from __future__ import annotations

from unittest.mock import AsyncMock

from fastapi import status
from httpx import AsyncClient
from openai import OpenAIError

from app.services.message import TITLE_TRUNCATE_LENGTH
from tests.conftest import create_agent_and_session, mock_chat_completion


async def test_send_message_empty_content(client_with_openai: AsyncClient) -> None:
    _, session_id = await create_agent_and_session(client_with_openai)
    response = await client_with_openai.post(
        f"/api/v1/sessions/{session_id}/messages/",
        json={"content": ""},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


async def test_send_message_content_too_long(client_with_openai: AsyncClient) -> None:
    _, session_id = await create_agent_and_session(client_with_openai)
    response = await client_with_openai.post(
        f"/api/v1/sessions/{session_id}/messages/",
        json={"content": "x" * 50001},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


async def test_send_message(client_with_openai: AsyncClient, mock_openai: AsyncMock) -> None:
    _, session_id = await create_agent_and_session(client_with_openai)
    mock_chat_completion(mock_openai, "Hello back")

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


async def test_send_message_session_not_found(client_with_openai: AsyncClient) -> None:
    response = await client_with_openai.post(
        "/api/v1/sessions/9999/messages/",
        json={"content": "Hello"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_get_messages(client_with_openai: AsyncClient, mock_openai: AsyncMock) -> None:
    _, session_id = await create_agent_and_session(client_with_openai)
    mock_chat_completion(mock_openai, "Response")

    await client_with_openai.post(f"/api/v1/sessions/{session_id}/messages/", json={"content": "First"})
    await client_with_openai.post(f"/api/v1/sessions/{session_id}/messages/", json={"content": "Second"})

    response = await client_with_openai.get(f"/api/v1/sessions/{session_id}/messages/")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    # 2 user messages × 2 (user + assistant) = 4 total
    assert len(body["items"]) == 4  # noqa: PLR2004
    assert body["total"] == 4  # noqa: PLR2004


async def test_get_messages_session_not_found(client_with_openai: AsyncClient) -> None:
    response = await client_with_openai.get("/api/v1/sessions/9999/messages/")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_get_messages_empty(client_with_openai: AsyncClient) -> None:
    _, session_id = await create_agent_and_session(client_with_openai)
    response = await client_with_openai.get(f"/api/v1/sessions/{session_id}/messages/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"items": [], "total": 0}


async def test_send_message_openai_error(client_with_openai: AsyncClient, mock_openai: AsyncMock) -> None:
    _, session_id = await create_agent_and_session(client_with_openai)
    mock_openai.chat.completions.create = AsyncMock(side_effect=OpenAIError("API failure"))

    response = await client_with_openai.post(
        f"/api/v1/sessions/{session_id}/messages/",
        json={"content": "Hello"},
    )
    assert response.status_code == status.HTTP_502_BAD_GATEWAY
    data = response.json()
    assert data["code"] == "OPENAI_ERROR"


async def test_send_message_openai_unconfigured(
    client_without_openai: AsyncClient,
) -> None:
    response = await client_without_openai.post(
        "/api/v1/sessions/1/messages/",
        json={"content": "Hello"},
    )
    assert response.status_code == status.HTTP_502_BAD_GATEWAY
    data = response.json()
    assert data["code"] == "OPENAI_ERROR"


async def test_send_message_openai_error_does_not_persist(
    client_with_openai: AsyncClient, mock_openai: AsyncMock
) -> None:
    _, session_id = await create_agent_and_session(client_with_openai)
    mock_openai.chat.completions.create = AsyncMock(side_effect=OpenAIError("API failure"))

    await client_with_openai.post(f"/api/v1/sessions/{session_id}/messages/", json={"content": "Hello"})

    response = await client_with_openai.get(f"/api/v1/sessions/{session_id}/messages/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["items"] == []


async def test_get_messages_pagination(client_with_openai: AsyncClient, mock_openai: AsyncMock) -> None:
    _, session_id = await create_agent_and_session(client_with_openai)
    mock_chat_completion(mock_openai, "Response")

    for i in range(5):
        await client_with_openai.post(f"/api/v1/sessions/{session_id}/messages/", json={"content": f"msg {i}"})

    response = await client_with_openai.get(f"/api/v1/sessions/{session_id}/messages/?skip=0&limit=2")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert len(body["items"]) == 2  # noqa: PLR2004
    assert body["total"] == 10  # noqa: PLR2004


async def test_get_messages_desc_order(client_with_openai: AsyncClient, mock_openai: AsyncMock) -> None:
    _, session_id = await create_agent_and_session(client_with_openai)
    mock_chat_completion(mock_openai, "Response")

    for i in range(5):
        await client_with_openai.post(f"/api/v1/sessions/{session_id}/messages/", json={"content": f"msg {i}"})

    response = await client_with_openai.get(f"/api/v1/sessions/{session_id}/messages/?order=desc&limit=3")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert len(body["items"]) == 3  # noqa: PLR2004
    assert body["total"] == 10  # noqa: PLR2004
    # With desc order, newest messages come first
    ids = [msg["id"] for msg in body["items"]]
    assert ids == sorted(ids, reverse=True)


async def test_session_title_set_on_first_message(
    client_with_openai: AsyncClient,
    mock_openai: AsyncMock,
) -> None:
    _, session_id = await create_agent_and_session(client_with_openai)
    mock_chat_completion(mock_openai, "Assistant reply")

    await client_with_openai.post(
        f"/api/v1/sessions/{session_id}/messages/",
        json={"content": "Hello, this is my first message in the session"},
    )

    session_resp = await client_with_openai.get(f"/api/v1/sessions/{session_id}")
    assert session_resp.status_code == status.HTTP_200_OK
    expected_title = "Hello, this is my first message in the session"[:TITLE_TRUNCATE_LENGTH]
    assert session_resp.json()["title"] == expected_title


async def test_session_title_unchanged_on_subsequent_messages(
    client_with_openai: AsyncClient,
    mock_openai: AsyncMock,
) -> None:
    _, session_id = await create_agent_and_session(client_with_openai)
    mock_chat_completion(mock_openai, "Assistant reply")

    await client_with_openai.post(
        f"/api/v1/sessions/{session_id}/messages/",
        json={"content": "First message"},
    )
    await client_with_openai.post(
        f"/api/v1/sessions/{session_id}/messages/",
        json={"content": "Second message"},
    )

    session_resp = await client_with_openai.get(f"/api/v1/sessions/{session_id}")
    assert session_resp.json()["title"] == "First message"
