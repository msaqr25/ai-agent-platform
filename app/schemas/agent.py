from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

DEFAULT_AGENT_PROMPT = "You are a helpful AI assistant."


class AgentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    prompt: str = Field(default=DEFAULT_AGENT_PROMPT, min_length=1, max_length=10000)


class AgentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(None, min_length=1, max_length=255)
    prompt: str | None = Field(None, min_length=1, max_length=10000)

    @model_validator(mode="after")
    def _require_at_least_one_field(self) -> Self:
        if self.name is None and self.prompt is None:
            raise ValueError("At least one of 'name' or 'prompt' must be provided")
        return self


class AgentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    prompt: str
    created_at: datetime
    updated_at: datetime
