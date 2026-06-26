from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from openai import AsyncOpenAI

from app.core.config import settings
from app.core.errors import OpenAIException


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
