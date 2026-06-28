from fastapi import APIRouter, File, UploadFile, status

from app.core.config import settings
from app.core.dependencies import GetDB, GetVoiceService, OpenAIClient
from app.core.validators import read_and_validate_audio
from app.schemas.message import MessageResponse, VoiceResponse

router = APIRouter(prefix="/sessions/{session_id}/voice", tags=["voice"])


@router.post("/", response_model=VoiceResponse, status_code=status.HTTP_201_CREATED)
async def process_voice_message(
    session_id: int,
    db: GetDB,
    openai_client: OpenAIClient,
    voice: GetVoiceService,
    audio: UploadFile = File(),  # noqa: B008
) -> VoiceResponse:
    """Upload audio for transcription, send as message, and return the AI reply with synthesised speech."""
    audio_bytes = await read_and_validate_audio(audio, settings.MAX_AUDIO_FILE_SIZE)

    user_msg, assistant_msg = await voice.process_voice_message(
        session_id,
        audio_bytes,
        str(audio.content_type),
        db,
        openai_client,
    )

    return VoiceResponse(
        user_message=MessageResponse.model_validate(user_msg),
        assistant_message=MessageResponse.model_validate(assistant_msg),
    )
