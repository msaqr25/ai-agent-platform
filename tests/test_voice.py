from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest_asyncio
from fastapi import status
from httpx import AsyncClient


@pytest_asyncio.fixture(autouse=True)
async def mock_aiofiles():
    with patch("aiofiles.open") as mock_open:
        mock_cm = AsyncMock()
        mock_file = AsyncMock()
        mock_cm.__aenter__.return_value = mock_file
        mock_open.return_value = mock_cm
        yield


async def _create_agent_and_session(client: AsyncClient) -> int:
    agent_resp = await client.post("/api/v1/agents/", json={"name": "Test Agent"})
    agent_id = agent_resp.json()["id"]
    session_resp = await client.post("/api/v1/sessions/", json={"agent_id": agent_id})
    return session_resp.json()["id"]


async def test_process_voice_message(client_with_openai: AsyncClient, mock_openai: AsyncMock) -> None:
    session_id = await _create_agent_and_session(client_with_openai)

    mock_transcript = MagicMock()
    mock_transcript.text = "test transcript"
    mock_openai.audio.transcriptions.create = AsyncMock(return_value=mock_transcript)

    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "test response"
    mock_completion.choices = [mock_choice]
    mock_openai.chat.completions.create = AsyncMock(return_value=mock_completion)

    mock_tts = MagicMock()
    mock_tts.content = b"fake audio bytes"
    mock_openai.audio.speech.create = AsyncMock(return_value=mock_tts)

    audio_bytes = b"fake audio data"
    response = await client_with_openai.post(
        f"/api/v1/sessions/{session_id}/voice/",
        files={"audio": ("test.wav", audio_bytes, "audio/wav")},
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "user_message" in data
    assert data["user_message"]["role"] == "user"
    assert data["user_message"]["content"] == "test transcript"
    assert "assistant_message" in data
    assert data["assistant_message"]["role"] == "assistant"
    assert "audio_file" in data
    assert data["audio_file"]["mime_type"] == "audio/mpeg"
    assert "id" in data["audio_file"]
    assert "filename" in data["audio_file"]
    assert "file_path" in data["audio_file"]
    assert "file_size" in data["audio_file"]
    assert data["audio_file"]["message_id"] == data["assistant_message"]["id"]


async def test_voice_invalid_session(client_with_openai: AsyncClient) -> None:
    audio_bytes = b"fake audio data"
    response = await client_with_openai.post(
        "/api/v1/sessions/9999/voice/",
        files={"audio": ("test.wav", audio_bytes, "audio/wav")},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
