from __future__ import annotations

from fastapi import UploadFile

from app.core.errors import BadRequestException

MIME_TO_EXT: dict[str, str] = {
    "audio/wav": ".wav",
    "audio/mpeg": ".mp3",
    "audio/ogg": ".ogg",
    "audio/webm": ".webm",
}

CHUNK_SIZE = 8 * 1024


def validate_mime_type(mime_type: str | None) -> str:
    if mime_type is None:
        raise BadRequestException(detail="Missing audio content type", code="INVALID_MIME_TYPE")
    ext = MIME_TO_EXT.get(mime_type)
    if ext is None:
        allowed = ", ".join(sorted(MIME_TO_EXT))
        raise BadRequestException(
            detail=f"Unsupported audio format: {mime_type}. Allowed: {allowed}",
            code="INVALID_MIME_TYPE",
        )
    return ext


def validate_audio_file_size(total: int, max_size: int) -> None:
    if total > max_size:
        raise BadRequestException(
            detail=f"Audio file too large (max {max_size // (1024 * 1024)} MB)",
            code="FILE_TOO_LARGE",
        )


def validate_audio_not_empty(total: int) -> None:
    if total == 0:
        raise BadRequestException(detail="Audio file is empty", code="EMPTY_FILE")


async def read_and_validate_audio(upload: UploadFile, max_size: int) -> bytes:
    """Read upload stream, validate MIME type and size, return the raw bytes."""
    validate_mime_type(upload.content_type)

    total = 0
    chunks: list[bytes] = []
    while chunk := await upload.read(CHUNK_SIZE):
        total += len(chunk)
        validate_audio_file_size(total, max_size)
        chunks.append(chunk)

    validate_audio_not_empty(total)
    return b"".join(chunks)
