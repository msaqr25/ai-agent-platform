from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.message import MessageResponse


class AudioFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    message_id: int
    filename: str
    file_path: str
    mime_type: str
    file_size: int
    created_at: datetime


class VoiceResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse
    audio_file: AudioFileResponse
