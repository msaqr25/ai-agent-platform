from fastapi import APIRouter, Query, status

from app.core.database import GetDB
from app.schemas.chat_session import ChatSessionCreate, ChatSessionResponse
from app.services.chat_session import chat_session_service

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(data: ChatSessionCreate, db: GetDB) -> ChatSessionResponse:
    session = await chat_session_service.create_session(data, db)
    return ChatSessionResponse.model_validate(session)


@router.get("/agent/{agent_id}", response_model=list[ChatSessionResponse])
async def list_sessions_for_agent(
    agent_id: int,
    db: GetDB,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> list[ChatSessionResponse]:
    sessions = await chat_session_service.list_sessions_for_agent(agent_id, db, skip=skip, limit=limit)
    return [ChatSessionResponse.model_validate(session) for session in sessions]


@router.get("/{session_id}", response_model=ChatSessionResponse)
async def get_session(session_id: int, db: GetDB) -> ChatSessionResponse:
    session = await chat_session_service.get_session(session_id, db)
    return ChatSessionResponse.model_validate(session)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: int, db: GetDB) -> None:
    await chat_session_service.delete_session(session_id, db)
