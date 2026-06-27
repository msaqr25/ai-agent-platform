from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audio_file import AudioFile
from app.repositories.base import BaseRepository


class AudioFileRepository(BaseRepository[AudioFile]):
    def __init__(self) -> None:
        super().__init__(AudioFile)

    async def get_by_content_hash(self, db: AsyncSession, content_hash: str) -> AudioFile | None:
        stmt = select(AudioFile).where(AudioFile.content_hash == content_hash)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
