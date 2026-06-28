from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.errors import OpenAIException
from app.repositories.agent import AgentRepository
from app.repositories.audio_file import AudioFileRepository
from app.repositories.chat_session import ChatSessionRepository
from app.repositories.message import MessageRepository
from app.services.agent import AgentService
from app.services.chat_session import ChatSessionService
from app.services.message import MessageService
from app.services.voice import VoiceService


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


GetDB = Annotated[AsyncSession, Depends(get_db)]


async def get_openai_client() -> AsyncGenerator[AsyncOpenAI]:
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise OpenAIException(detail="OpenAI client is not configured")
    client = AsyncOpenAI(api_key=api_key.get_secret_value())

    try:
        yield client
    finally:
        await client.close()


OpenAIClient = Annotated[AsyncOpenAI, Depends(get_openai_client)]


async def get_agent_service() -> AgentService:
    return AgentService(AgentRepository())


GetAgentService = Annotated[AgentService, Depends(get_agent_service)]


async def get_chat_session_service(
    agent_service: GetAgentService,
) -> ChatSessionService:
    return ChatSessionService(ChatSessionRepository(), agent_service)


GetChatSessionService = Annotated[ChatSessionService, Depends(get_chat_session_service)]


async def get_message_service(sessions: GetChatSessionService) -> MessageService:
    return MessageService(MessageRepository(), sessions)


GetMessageService = Annotated[MessageService, Depends(get_message_service)]


async def get_voice_service(sessions: GetChatSessionService, messages: GetMessageService) -> VoiceService:
    return VoiceService(AudioFileRepository(), sessions, messages)


GetVoiceService = Annotated[VoiceService, Depends(get_voice_service)]
