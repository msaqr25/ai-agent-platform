from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi import status
from httpx import AsyncClient


# aiofiles.open is an async context manager — patch it so that
# __aenter__ returns a mock file handle, preventing actual disk I/O.
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


async def _setup_mock_openai(mock_openai: AsyncMock) -> None:
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


async def test_process_voice_message(client_with_openai: AsyncClient, mock_openai: AsyncMock) -> None:
    session_id = await _create_agent_and_session(client_with_openai)
    await _setup_mock_openai(mock_openai)

    response = await client_with_openai.post(
        f"/api/v1/sessions/{session_id}/voice/",
        files={"audio": ("test.wav", b"fake audio data", "audio/wav")},
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
    session_id = await _create_agent_and_session(client_with_openai)
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
    session_id = await _create_agent_and_session(client_with_openai)
    response = await client_with_openai.post(
        f"/api/v1/sessions/{session_id}/voice/",
        files={"audio": ("test.wav", b"fake audio data", mime_type)},
    )
    assert response.status_code == 400  # noqa: PLR2004
    data = response.json()
    assert data["code"] == expected_code


async def test_voice_empty_file(
    client_with_openai: AsyncClient,
) -> None:
    session_id = await _create_agent_and_session(client_with_openai)
    response = await client_with_openai.post(
        f"/api/v1/sessions/{session_id}/voice/",
        files={"audio": ("test.wav", b"", "audio/wav")},
    )
    assert response.status_code == 400  # noqa: PLR2004
    data = response.json()
    assert data["code"] == "EMPTY_FILE"


async def test_voice_file_too_large(
    client_with_openai: AsyncClient,
) -> None:
    session_id = await _create_agent_and_session(client_with_openai)
    oversized = b"x" * (10 * 1024 * 1024 + 1)
    response = await client_with_openai.post(
        f"/api/v1/sessions/{session_id}/voice/",
        files={"audio": ("test.wav", oversized, "audio/wav")},
    )
    assert response.status_code == 400  # noqa: PLR2004
    data = response.json()
    assert data["code"] == "FILE_TOO_LARGE"
