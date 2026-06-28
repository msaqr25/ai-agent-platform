from typing import cast

from openai import AsyncOpenAI
from openai import OpenAIError as OpenAISDKError
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import OpenAIException
from app.core.logger import get_logger
from app.models.message import Message, MessageRole
from app.repositories.message import MessageRepository
from app.services.chat_session import ChatSessionService, chat_session_service

TITLE_TRUNCATE_LENGTH: int = 60

logger = get_logger(__name__)


class MessageService:
    def __init__(
        self,
        repository: MessageRepository | None = None,
        sessions: ChatSessionService | None = None,
    ) -> None:
        self.repository = repository or MessageRepository()
        self.sessions = sessions or chat_session_service

    async def get_messages(
        self, session_id: int, db: AsyncSession, skip: int = 0, limit: int = 50, order: str = "asc"
    ) -> tuple[list[Message], int]:
        await self.sessions.get_session(session_id, db)
        items = await self.repository.get_by_session_id(db, session_id, skip=skip, limit=limit, order=order)
        total = await self.repository.count_by_session_id(db, session_id)
        return items, total

    async def send_message(
        self,
        session_id: int,
        content: str,
        db: AsyncSession,
        openai_client: AsyncOpenAI,
    ) -> tuple[Message, Message]:
        session = await self.sessions.get_session_with_agent(session_id, db)
        history = await self.repository.get_by_session_id(db, session_id, load_audio=False)
        openai_messages = self._build_openai_messages(session.agent.prompt, history, content)

        user_message = await self.repository.create(
            db,
            {"session_id": session_id, "role": MessageRole.user, "content": content},
        )

        completion = await self._call_openai(openai_client, openai_messages)
        assistant_reply = self._validate_response(completion)

        assistant_message = await self.repository.create(
            db,
            {"session_id": session_id, "role": MessageRole.assistant, "content": assistant_reply},
        )

        if not history:
            await self.sessions.update_title(session, content.strip()[:TITLE_TRUNCATE_LENGTH])

        await self.sessions.touch_session(session)

        logger.info(
            "Message sent",
            extra={
                "session_id": session_id,
                "user_message_length": len(content),
                "assistant_response_length": len(assistant_reply),
            },
        )

        return user_message, assistant_message

    async def _call_openai(
        self,
        openai_client: AsyncOpenAI,
        messages: list[ChatCompletionMessageParam],
    ) -> ChatCompletion:
        try:
            return await openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL_NAME,
                messages=messages,
            )
        except OpenAISDKError as exc:
            raise OpenAIException() from exc

    def _validate_response(self, completion: ChatCompletion) -> str:
        if not completion.choices:
            raise OpenAIException(detail="OpenAI response contained no choices")
        reply = completion.choices[0].message.content
        if reply is None:
            raise OpenAIException(detail="OpenAI response did not include message content")
        if not reply.strip():
            raise OpenAIException(detail="OpenAI response contained empty message content")
        return reply

    def _build_openai_messages(
        self,
        agent_prompt: str,
        history: list[Message],
        content: str,
    ) -> list[ChatCompletionMessageParam]:
        messages: list[dict[str, str]] = [{"role": "system", "content": agent_prompt}]
        messages.extend({"role": message.role.value, "content": message.content} for message in history)
        messages.append({"role": "user", "content": content})
        return cast(list[ChatCompletionMessageParam], messages)


message_service = MessageService()
