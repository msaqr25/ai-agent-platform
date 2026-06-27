from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.message import Message
from app.repositories.base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    def __init__(self) -> None:
        super().__init__(Message)

    async def get_by_session_id(
        self, db: AsyncSession, session_id: int, skip: int = 0, limit: int = 1000, *, load_audio: bool = True
    ) -> list[Message]:
        stmt = select(Message).where(Message.session_id == session_id).order_by(Message.created_at.asc())
        if load_audio:
            stmt = stmt.options(joinedload(Message.audio_file))
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())
