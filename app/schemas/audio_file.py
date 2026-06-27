from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AudioFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    message_id: int
    filename: str
    file_path: str
    mime_type: str
    file_size: int
    created_at: datetime
