from app.models.agent import Agent
from app.repositories.base import BaseRepository


class AgentRepository(BaseRepository[Agent]):
    def __init__(self) -> None:
        super().__init__(Agent)
