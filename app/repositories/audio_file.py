from app.models.audio_file import AudioFile
from app.repositories.base import BaseRepository


class AudioFileRepository(BaseRepository[AudioFile]):
    def __init__(self) -> None:
        super().__init__(AudioFile)
