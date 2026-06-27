from fastapi import APIRouter, File, UploadFile, status

from app.core.config import settings
from app.core.database import GetDB
from app.core.openai import OpenAIClient
from app.core.validators import read_and_validate_audio
from app.schemas.audio_file import AudioFileResponse
from app.schemas.message import MessageResponse, VoiceResponse
from app.services.voice import voice_service

router = APIRouter(prefix="/sessions/{session_id}/voice", tags=["voice"])


@router.post("/", response_model=VoiceResponse, status_code=status.HTTP_201_CREATED)
async def process_voice_message(
    session_id: int,
    audio: UploadFile = File(),  # noqa: B008
    *,
    db: GetDB,
    openai_client: OpenAIClient,
) -> VoiceResponse:
    audio_bytes = await read_and_validate_audio(audio, settings.MAX_AUDIO_FILE_SIZE)

    audio_file, user_msg, assistant_msg = await voice_service.process_voice_message(
        session_id,
        audio_bytes,
        audio.content_type,  # ty: ignore[invalid-argument-type]
        db,
        openai_client,
    )

    await db.refresh(user_msg, ["audio_file"])
    await db.refresh(assistant_msg, ["audio_file"])
    return VoiceResponse(
        user_message=MessageResponse.model_validate(user_msg),
        assistant_message=MessageResponse.model_validate(assistant_msg),
        audio_file=AudioFileResponse.model_validate(audio_file),
    )
