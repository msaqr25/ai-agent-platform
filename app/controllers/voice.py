from fastapi import APIRouter, File, UploadFile, status

from app.core.config import settings
from app.core.constants import ALLOWED_AUDIO_MIME_TYPES
from app.core.database import GetDB
from app.core.errors import BadRequestException
from app.core.openai import OpenAIClient
from app.schemas.audio_file import AudioFileResponse, VoiceResponse
from app.schemas.message import MessageResponse
from app.services.voice import voice_service

router = APIRouter(prefix="/sessions/{session_id}/voice", tags=["voice"])
CHUNK_SIZE = 8 * 1024


@router.post("/", response_model=VoiceResponse, status_code=status.HTTP_201_CREATED)
async def process_voice_message(
    session_id: int,
    audio: UploadFile = File(),  # noqa: B008
    *,
    db: GetDB,
    openai_client: OpenAIClient,
) -> VoiceResponse:
    if audio.content_type not in ALLOWED_AUDIO_MIME_TYPES:
        raise BadRequestException(
            detail=f"Unsupported audio format: {audio.content_type}. Allowed: {', '.join(ALLOWED_AUDIO_MIME_TYPES)}",
            code="INVALID_MIME_TYPE",
        )

    total = 0
    chunks: list[bytes] = []
    while chunk := await audio.read(CHUNK_SIZE):
        total += len(chunk)
        if total > settings.MAX_AUDIO_FILE_SIZE:
            raise BadRequestException(
                detail=f"Audio file too large (max {settings.MAX_AUDIO_FILE_SIZE // (1024 * 1024)} MB)",
                code="FILE_TOO_LARGE",
            )
        chunks.append(chunk)

    if total == 0:
        raise BadRequestException(detail="Audio file is empty", code="EMPTY_FILE")

    audio_bytes = b"".join(chunks)

    audio_file, user_msg, assistant_msg = await voice_service.process_voice_message(
        session_id,
        audio_bytes,
        audio.content_type,
        db,
        openai_client,
    )

    return VoiceResponse(
        user_message=MessageResponse.model_validate(user_msg),
        assistant_message=MessageResponse.model_validate(assistant_msg),
        audio_file=AudioFileResponse.model_validate(audio_file),
    )
