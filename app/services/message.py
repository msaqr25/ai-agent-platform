from typing import cast

from openai import AsyncOpenAI
from openai import OpenAIError as OpenAISDKError
from openai.types.chat import ChatCompletionMessageParam
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import OpenAIException
from app.core.logger import get_logger
from app.models.message import Message, MessageRole
from app.repositories.message import MessageRepository
from app.services.agent import AgentService, agent_service
from app.services.chat_session import ChatSessionService, chat_session_service

logger = get_logger(__name__)


class MessageService:
    def __init__(
        self,
        repository: MessageRepository | None = None,
        sessions: ChatSessionService | None = None,
        agents: AgentService | None = None,
    ) -> None:
        self.repository = repository or MessageRepository()
        self.sessions = sessions or chat_session_service
        self.agents = agents or agent_service

    async def get_messages(self, session_id: int, db: AsyncSession) -> list[Message]:
        await self.sessions.get_session(session_id, db)
        return await self.repository.get_by_session_id(db, session_id)

    async def send_message(
        self,
        session_id: int,
        content: str,
        db: AsyncSession,
        openai_client: AsyncOpenAI,
    ) -> tuple[Message, Message]:
        session = await self.sessions.get_session(session_id, db)
        agent = await self.agents.get_agent(session.agent_id, db)
        history = await self.repository.get_by_session_id(db, session_id)
        openai_messages = self._build_openai_messages(agent.prompt, history, content)

        user_message = await self.repository.create(
            db,
            {"session_id": session_id, "role": MessageRole.user, "content": content},
        )

        try:
            completion = await openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL_NAME,
                messages=openai_messages,
            )
        except OpenAISDKError as exc:
            raise OpenAIException() from exc

        if not completion.choices:
            raise OpenAIException(detail="OpenAI response contained no choices")

        assistant_reply = completion.choices[0].message.content
        if assistant_reply is None:
            raise OpenAIException(detail="OpenAI response did not include message content")

        assistant_message = await self.repository.create(
            db,
            {"session_id": session_id, "role": MessageRole.assistant, "content": assistant_reply},
        )

        if not history:
            await self.sessions.update_title(session_id, content.strip()[:60], db)

        logger.info(
            "Message sent",
            extra={
                "session_id": session_id,
                "user_message_length": len(content),
                "assistant_response_length": len(assistant_reply),
            },
        )

        return user_message, assistant_message

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
