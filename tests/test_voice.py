from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import status
from httpx import AsyncClient

from tests.conftest import create_agent_and_session, mock_chat_completion


async def _setup_mock_openai(mock_openai: AsyncMock) -> None:
    mock_transcript = MagicMock()
    mock_transcript.text = "test transcript"
    mock_openai.audio.transcriptions.create = AsyncMock(return_value=mock_transcript)

    mock_chat_completion(mock_openai, "test response")

    mock_tts = MagicMock()
    mock_tts.content = b"fake audio bytes"
    mock_openai.audio.speech.create = AsyncMock(return_value=mock_tts)


async def test_process_voice_message(client_with_openai: AsyncClient, mock_openai: AsyncMock) -> None:
    _, session_id = await create_agent_and_session(client_with_openai)
    await _setup_mock_openai(mock_openai)

    response = await client_with_openai.post(
        f"/api/v1/sessions/{session_id}/voice/",
        files={"audio": ("test.wav", b"fake audio data", "audio/wav")},
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["user_message"]["role"] == "user"
    assert data["user_message"]["content"] == "test transcript"
    assert data["assistant_message"]["role"] == "assistant"
    assert data["assistant_message"]["audio_file"]["mime_type"] == "audio/mpeg"
    assert "id" in data["assistant_message"]["audio_file"]
    assert "filename" in data["assistant_message"]["audio_file"]
    assert "file_path" in data["assistant_message"]["audio_file"]
    assert "file_size" in data["assistant_message"]["audio_file"]
    assert data["assistant_message"]["audio_file"]["message_id"] == data["assistant_message"]["id"]


async def test_voice_invalid_session(client_with_openai: AsyncClient) -> None:
    response = await client_with_openai.post(
        "/api/v1/sessions/9999/voice/",
        files={"audio": ("test.wav", b"fake audio data", "audio/wav")},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_voice_openai_unconfigured(client_without_openai: AsyncClient) -> None:
    response = await client_without_openai.post(
        "/api/v1/sessions/1/voice/",
        files={"audio": ("test.wav", b"fake audio data", "audio/wav")},
    )
    assert response.status_code == status.HTTP_502_BAD_GATEWAY
    data = response.json()
    assert data["code"] == "OPENAI_ERROR"


@pytest.mark.parametrize(
    ("filename", "audio_bytes", "mime_type", "expected_status"),
    [
        ("test.wav", b"fake audio data", "audio/wav", status.HTTP_201_CREATED),
        ("test.wav", b"fake audio data", "audio/mpeg", status.HTTP_201_CREATED),
        ("test.wav", b"fake audio data", "audio/ogg", status.HTTP_201_CREATED),
        ("test.wav", b"fake audio data", "audio/webm", status.HTTP_201_CREATED),
    ],
)
async def test_voice_valid_mime_types(  # noqa: PLR0913
    client_with_openai: AsyncClient,
    mock_openai: AsyncMock,
    filename: str,
    audio_bytes: bytes,
    mime_type: str,
    expected_status: int,
) -> None:
    _, session_id = await create_agent_and_session(client_with_openai)
    await _setup_mock_openai(mock_openai)
    response = await client_with_openai.post(
        f"/api/v1/sessions/{session_id}/voice/",
        files={"audio": (filename, audio_bytes, mime_type)},
    )
    assert response.status_code == expected_status


@pytest.mark.parametrize(
    ("mime_type", "expected_code"),
    [
        ("video/mp4", "INVALID_MIME_TYPE"),
        ("audio/flac", "INVALID_MIME_TYPE"),
        ("application/pdf", "INVALID_MIME_TYPE"),
    ],
)
async def test_voice_invalid_mime_type(
    client_with_openai: AsyncClient,
    mime_type: str,
    expected_code: str,
) -> None:
    _, session_id = await create_agent_and_session(client_with_openai)
    response = await client_with_openai.post(
        f"/api/v1/sessions/{session_id}/voice/",
        files={"audio": ("test.wav", b"fake audio data", mime_type)},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["code"] == expected_code


async def test_voice_empty_file(
    client_with_openai: AsyncClient,
) -> None:
    _, session_id = await create_agent_and_session(client_with_openai)
    response = await client_with_openai.post(
        f"/api/v1/sessions/{session_id}/voice/",
        files={"audio": ("test.wav", b"", "audio/wav")},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["code"] == "EMPTY_FILE"


async def test_voice_file_too_large(
    client_with_openai: AsyncClient,
) -> None:
    _, session_id = await create_agent_and_session(client_with_openai)
    oversized = b"x" * (10 * 1024 * 1024 + 1)
    response = await client_with_openai.post(
        f"/api/v1/sessions/{session_id}/voice/",
        files={"audio": ("test.wav", oversized, "audio/wav")},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["code"] == "FILE_TOO_LARGE"
