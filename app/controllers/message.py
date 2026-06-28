from fastapi import APIRouter, Query, status

from app.core.database import GetDB
from app.core.openai import OpenAIClient
from app.schemas.message import MessageCreate, MessageResponse, SendMessageResponse
from app.schemas.pagination import PaginatedResponse
from app.services.message import message_service

router = APIRouter(prefix="/sessions/{session_id}/messages", tags=["messages"])


@router.get("/", response_model=PaginatedResponse[MessageResponse])
async def get_messages(
    session_id: int,
    db: GetDB,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    order: str = Query("asc", pattern="^(asc|desc)$"),
) -> PaginatedResponse[MessageResponse]:
    messages, total = await message_service.get_messages(session_id, db, skip=skip, limit=limit, order=order)
    return PaginatedResponse(
        items=[MessageResponse.model_validate(message) for message in messages],
        total=total,
    )


@router.post("/", response_model=SendMessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    session_id: int,
    data: MessageCreate,
    db: GetDB,
    openai_client: OpenAIClient,
) -> SendMessageResponse:
    user_message, assistant_message = await message_service.send_message(session_id, data.content, db, openai_client)
    return SendMessageResponse(
        user_message=MessageResponse.model_validate(user_message),
        assistant_message=MessageResponse.model_validate(assistant_message),
    )
