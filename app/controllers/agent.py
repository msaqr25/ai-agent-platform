from fastapi import APIRouter, Query, status

from app.core.dependencies import GetAgentService, GetDB
from app.schemas.agent import AgentCreate, AgentResponse, AgentUpdate
from app.schemas.pagination import PaginatedResponse

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(data: AgentCreate, db: GetDB, agent_service: GetAgentService) -> AgentResponse:
    agent = await agent_service.create_agent(data, db)
    return AgentResponse.model_validate(agent)


@router.get("/", response_model=PaginatedResponse[AgentResponse])
async def list_agents(
    db: GetDB,
    agent_service: GetAgentService,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> PaginatedResponse[AgentResponse]:
    agents, total = await agent_service.list_agents(db, skip=skip, limit=limit)
    return PaginatedResponse(
        items=[AgentResponse.model_validate(agent) for agent in agents],
        total=total,
    )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: int, db: GetDB, agent_service: GetAgentService) -> AgentResponse:
    agent = await agent_service.get_agent(agent_id, db)
    return AgentResponse.model_validate(agent)


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: int, data: AgentUpdate, db: GetDB, agent_service: GetAgentService) -> AgentResponse:
    agent = await agent_service.update_agent(agent_id, data, db)
    return AgentResponse.model_validate(agent)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(agent_id: int, db: GetDB, agent_service: GetAgentService) -> None:
    await agent_service.delete_agent(agent_id, db)
