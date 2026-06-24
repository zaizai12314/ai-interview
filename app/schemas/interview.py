import uuid
from datetime import datetime
from pydantic import BaseModel

class InterviewCreate(BaseModel):
    resume_id: uuid.UUID
    target_job: str

class AnswerSubmit(BaseModel):
    answer: str

class InterviewResponse(BaseModel):
    id: uuid.UUID
    resume_id: uuid.UUID
    target_job: str
    status: str
    total_rounds: int
    history: list[dict] | None = None
    report: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    model_config = {"from_attributes": True}
