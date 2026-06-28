from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.message import MessageRole
from app.schemas.audio_file import AudioFileResponse


class MessageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=1, max_length=50000)


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    role: MessageRole
    content: str
    created_at: datetime
    audio_file: AudioFileResponse | None = None


class SendMessageResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse


class VoiceResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse
    audio_file: AudioFileResponse
