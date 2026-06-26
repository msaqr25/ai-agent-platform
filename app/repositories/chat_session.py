from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_session import ChatSession
from app.repositories.base import BaseRepository


class ChatSessionRepository(BaseRepository[ChatSession]):
    def __init__(self) -> None:
        super().__init__(ChatSession)

    async def get_by_agent_id(self, db: AsyncSession, agent_id: int) -> list[ChatSession]:
        stmt = select(ChatSession).where(ChatSession.agent_id == agent_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())
