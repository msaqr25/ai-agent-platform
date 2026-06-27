from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.chat_session import ChatSession
from app.repositories.base import BaseRepository


class ChatSessionRepository(BaseRepository[ChatSession]):
    def __init__(self) -> None:
        super().__init__(ChatSession)

    async def get_by_id_with_agent(self, db: AsyncSession, id: int) -> ChatSession | None:
        stmt = select(ChatSession).options(joinedload(ChatSession.agent)).where(ChatSession.id == id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_agent_id(
        self, db: AsyncSession, agent_id: int, skip: int = 0, limit: int = 100
    ) -> list[ChatSession]:
        stmt = (
            select(ChatSession)
            .where(ChatSession.agent_id == agent_id)
            .order_by(ChatSession.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
