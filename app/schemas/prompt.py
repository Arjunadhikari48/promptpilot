from datetime import datetime
from pydantic import BaseModel, Field


class PromptBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    content: str = Field(min_length=1)
    tags: str | None = None


class PromptCreate(PromptBase):
    pass


class PromptUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    content: str | None = Field(default=None, min_length=1)
    tags: str | None = None


class PromptRead(PromptBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
