from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundException
from app.models.chat_session import ChatSession
from app.repositories.chat_session import ChatSessionRepository
from app.schemas.chat_session import ChatSessionCreate
from app.services.agent import AgentService, agent_service


class ChatSessionService:
    def __init__(
        self,
        repository: ChatSessionRepository | None = None,
        agents: AgentService | None = None,
    ) -> None:
        self.repository = repository or ChatSessionRepository()
        self.agents = agents or agent_service

    async def create_session(self, data: ChatSessionCreate, db: AsyncSession) -> ChatSession:
        await self.agents.get_agent(data.agent_id, db)
        return await self.repository.create(db, data.model_dump())

    async def list_sessions_for_agent(
        self, agent_id: int, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> list[ChatSession]:
        return await self.repository.get_by_agent_id(db, agent_id, skip=skip, limit=limit)

    async def get_session_with_agent(self, session_id: int, db: AsyncSession) -> ChatSession:
        session = await self.repository.get_by_id_with_agent(db, session_id)
        if session is None:
            raise NotFoundException(detail=f"Chat session {session_id} not found")
        return session

    async def get_session(self, session_id: int, db: AsyncSession) -> ChatSession:
        session = await self.repository.get_by_id(db, session_id)
        if session is None:
            raise NotFoundException(detail=f"Chat session {session_id} not found")
        return session

    async def update_title(
        self,
        session: ChatSession,
        title: str,
    ) -> None:
        session.title = title

    async def touch_session(
        self,
        session: ChatSession,
    ) -> None:
        session.updated_at = datetime.now(UTC)

    async def delete_session(self, session_id: int, db: AsyncSession) -> None:
        await self.get_session(session_id, db)
        await self.repository.delete(db, session_id)


chat_session_service = ChatSessionService()
