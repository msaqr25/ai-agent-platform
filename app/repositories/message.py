from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.repositories.base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    def __init__(self) -> None:
        super().__init__(Message)

    async def get_by_session_id(self, db: AsyncSession, session_id: int) -> list[Message]:
        stmt = select(Message).where(Message.session_id == session_id).order_by(Message.created_at.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())
