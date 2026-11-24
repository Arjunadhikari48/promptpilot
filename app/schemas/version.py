from datetime import datetime
from pydantic import BaseModel


class PromptVersionRead(BaseModel):
    id: int
    prompt_id: int
    version: int
    content: str
    created_at: datetime
    model_config = {"from_attributes": True}


class PromptVersionSummary(BaseModel):
    version: int
    created_at: datetime
    content_preview: str
    model_config = {"from_attributes": True}