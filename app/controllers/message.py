from fastapi import APIRouter, Query, status

from app.core.database import GetDB
from app.core.openai import OpenAIClient
from app.schemas.message import MessageCreate, MessageResponse, SendMessageResponse
from app.services.message import message_service

router = APIRouter(prefix="/sessions/{session_id}/messages", tags=["messages"])


@router.get("/", response_model=list[MessageResponse])
async def get_messages(
    session_id: int,
    db: GetDB,
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=5000),
) -> list[MessageResponse]:
    messages = await message_service.get_messages(session_id, db, skip=skip, limit=limit)
    return [MessageResponse.model_validate(message) for message in messages]


@router.post("/", response_model=SendMessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    session_id: int,
    data: MessageCreate,
    db: GetDB,
    openai_client: OpenAIClient,
) -> SendMessageResponse:
    user_message, assistant_message = await message_service.send_message(session_id, data.content, db, openai_client)
    await db.refresh(user_message, ["audio_file"])
    await db.refresh(assistant_message, ["audio_file"])
    return SendMessageResponse(
        user_message=MessageResponse.model_validate(user_message),
        assistant_message=MessageResponse.model_validate(assistant_message),
    )
