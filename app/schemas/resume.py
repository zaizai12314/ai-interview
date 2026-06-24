import uuid
from datetime import datetime
from pydantic import BaseModel

class ResumeResponse(BaseModel):
    id: uuid.UUID
    filename: str
    skills: list[str] | None = None
    experience: list[dict] | None = None
    education: list[dict] | dict | None = None
    parsed_at: datetime | None = None
    status: str = "pending"
    created_at: datetime
    model_config = {"from_attributes": True}

class JobMatch(BaseModel):
    title: str
    match_score: int
    reason: str