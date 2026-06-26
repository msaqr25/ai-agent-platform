from datetime import datetime

from pydantic import BaseModel, ConfigDict

DEFAULT_AGENT_PROMPT = "You are a helpful AI assistant."


class AgentCreate(BaseModel):
    name: str
    prompt: str = DEFAULT_AGENT_PROMPT


class AgentUpdate(BaseModel):
    name: str | None = None
    prompt: str | None = None


class AgentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    prompt: str
    created_at: datetime
    updated_at: datetime
