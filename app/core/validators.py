from __future__ import annotations

from fastapi import UploadFile

from app.core.errors import BadRequestException

MIME_TO_EXT: dict[str, str] = {
    "audio/wav": ".wav",
    "audio/mpeg": ".mp3",
    "audio/ogg": ".ogg",
    "audio/webm": ".webm",
}

ALLOWED_AUDIO_MIME_TYPES: frozenset[str] = frozenset(MIME_TO_EXT)

CHUNK_SIZE = 8 * 1024


def get_extension(mime_type: str) -> str:
    ext = MIME_TO_EXT.get(mime_type)
    if ext is None:
        raise BadRequestException(detail=f"Unsupported audio format: {mime_type}", code="INVALID_MIME_TYPE")
    return ext


def validate_audio_mime_type(content_type: str | None) -> None:
    if content_type not in ALLOWED_AUDIO_MIME_TYPES:
        raise BadRequestException(
            detail=f"Unsupported audio format: {content_type}. Allowed: {', '.join(sorted(ALLOWED_AUDIO_MIME_TYPES))}",
            code="INVALID_MIME_TYPE",
        )


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
    validate_audio_mime_type(upload.content_type)

    total = 0
    chunks: list[bytes] = []
    while chunk := await upload.read(CHUNK_SIZE):
        total += len(chunk)
        validate_audio_file_size(total, max_size)
        chunks.append(chunk)

    validate_audio_not_empty(total)
    return b"".join(chunks)
