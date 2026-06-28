from fastapi import APIRouter, Query, status

from app.core.dependencies import GetChatSessionService, GetDB
from app.schemas.chat_session import ChatSessionCreate, ChatSessionResponse
from app.schemas.pagination import PaginatedResponse

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    data: ChatSessionCreate,
    db: GetDB,
    sessions: GetChatSessionService,
) -> ChatSessionResponse:
    session = await sessions.create_session(data, db)
    return ChatSessionResponse.model_validate(session)


@router.get("/agent/{agent_id}", response_model=PaginatedResponse[ChatSessionResponse])
async def list_sessions_for_agent(
    agent_id: int,
    db: GetDB,
    sessions: GetChatSessionService,
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=500),
) -> PaginatedResponse[ChatSessionResponse]:
    items, total = await sessions.list_sessions_for_agent(agent_id, db, skip=skip, limit=limit)
    return PaginatedResponse(
        items=[ChatSessionResponse.model_validate(session) for session in items],
        total=total,
    )


@router.get("/{session_id}", response_model=ChatSessionResponse)
async def get_session(session_id: int, db: GetDB, sessions: GetChatSessionService) -> ChatSessionResponse:
    session = await sessions.get_session(session_id, db)
    return ChatSessionResponse.model_validate(session)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: int, db: GetDB, sessions: GetChatSessionService) -> None:
    await sessions.delete_session(session_id, db)
