from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundException
from app.core.logger import get_logger
from app.models.agent import Agent
from app.repositories.agent import AgentRepository
from app.schemas.agent import AgentCreate, AgentUpdate

logger = get_logger(__name__)


class AgentService:
    def __init__(self, repository: AgentRepository) -> None:
        self.repository = repository

    async def create_agent(self, data: AgentCreate, db: AsyncSession) -> Agent:
        agent = await self.repository.create(db, data.model_dump())
        logger.info("Agent created", extra={"agent_id": agent.id})
        return agent

    async def list_agents(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> tuple[list[Agent], int]:
        items = await self.repository.get_all(db, skip=skip, limit=limit)
        total = await self.repository.count(db)
        return items, total

    async def get_agent(self, agent_id: int, db: AsyncSession) -> Agent:
        agent = await self.repository.get_by_id(db, agent_id)
        if agent is None:
            raise NotFoundException(detail=f"Agent {agent_id} not found")
        return agent

    async def update_agent(self, agent_id: int, data: AgentUpdate, db: AsyncSession) -> Agent:
        updated_agent = await self.repository.update(db, agent_id, data.model_dump(exclude_unset=True))
        if updated_agent is None:
            raise NotFoundException(detail=f"Agent {agent_id} not found")
        return updated_agent

    async def delete_agent(self, agent_id: int, db: AsyncSession) -> None:
        agent = await self.get_agent(agent_id, db)
        await self.repository.delete(db, agent.id)
