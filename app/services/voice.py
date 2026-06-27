from __future__ import annotations

import uuid
from pathlib import Path

import aiofiles
from openai import AsyncOpenAI
from openai import OpenAIError as OpenAISDKError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import OpenAIException
from app.core.logger import get_logger
from app.core.validators import get_extension
from app.models.audio_file import AudioFile
from app.models.message import Message
from app.repositories.audio_file import AudioFileRepository
from app.services.chat_session import ChatSessionService, chat_session_service
from app.services.message import MessageService, message_service

logger = get_logger(__name__)


class VoiceService:
    def __init__(
        self,
        audio_repository: AudioFileRepository | None = None,
        sessions: ChatSessionService | None = None,
        messages: MessageService | None = None,
    ) -> None:
        self.audio_repository = audio_repository or AudioFileRepository()
        self.sessions = sessions or chat_session_service
        self.messages = messages or message_service

    async def _transcribe(
        self,
        audio_bytes: bytes,
        mime_type: str,
        openai_client: AsyncOpenAI,
    ) -> str:
        ext = get_extension(mime_type)
        stt_filename = f"input{ext}"
        try:
            transcript = await openai_client.audio.transcriptions.create(
                model=settings.OPENAI_STT_MODEL,
                file=(stt_filename, audio_bytes, mime_type),
            )
        except OpenAISDKError as exc:
            raise OpenAIException(detail="Speech-to-text request failed") from exc
        return transcript.text

    async def _synthesize(
        self,
        text: str,
        openai_client: AsyncOpenAI,
    ) -> bytes:
        try:
            tts_response = await openai_client.audio.speech.create(
                model=settings.OPENAI_TTS_MODEL,
                voice=settings.OPENAI_TTS_VOICE,
                input=text,
            )
        except OpenAISDKError as exc:
            raise OpenAIException(detail="Text-to-speech request failed") from exc
        return tts_response.content

    async def _save_audio_file(
        self,
        audio_bytes: bytes,
        mime_type: str,
        session_id: int,
        message_id: int,
        db: AsyncSession,
    ) -> AudioFile:
        ext = get_extension(mime_type)
        filename = f"{uuid.uuid4().hex}{ext}"
        session_dir = Path(settings.AUDIO_STORAGE_DIR) / str(session_id)
        session_dir.mkdir(parents=True, exist_ok=True)

        url_path = f"/audio/{session_id}/{filename}"

        audio_file = await self.audio_repository.create(
            db,
            {
                "filename": filename,
                "file_path": url_path,
                "mime_type": mime_type,
                "file_size": len(audio_bytes),
                "message_id": message_id,
            },
        )

        filepath = session_dir / filename
        async with aiofiles.open(filepath, "wb") as f:
            await f.write(audio_bytes)

        logger.info(
            "Audio file saved",
            extra={
                "audio_file_id": audio_file.id,
                "message_id": message_id,
                "session_id": session_id,
                "file_size": len(audio_bytes),
            },
        )

        return audio_file

    async def process_voice_message(
        self,
        session_id: int,
        audio_bytes: bytes,
        mime_type: str,
        db: AsyncSession,
        openai_client: AsyncOpenAI,
    ) -> tuple[AudioFile, Message, Message]:
        """Full voice pipeline: STT → chat response → TTS → persist audio file."""
        await self.sessions.get_session(session_id, db)

        transcript_text = await self._transcribe(audio_bytes, mime_type, openai_client)
        logger.info(
            "Transcription completed",
            extra={"session_id": session_id, "transcript_length": len(transcript_text)},
        )

        user_msg, assistant_msg = await self.messages.send_message(session_id, transcript_text, db, openai_client)

        tts_bytes = await self._synthesize(assistant_msg.content, openai_client)

        audio_file = await self._save_audio_file(
            tts_bytes,
            settings.OPENAI_TTS_OUTPUT_MIME,
            session_id,
            assistant_msg.id,
            db,
        )

        assistant_msg.audio_file = audio_file

        return audio_file, user_msg, assistant_msg


voice_service = VoiceService()
