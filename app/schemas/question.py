import uuid
from datetime import datetime
from pydantic import BaseModel

class QuestionCreate(BaseModel):
    content: str
    answer_hint: str | None = None
    job_title: str
    skills: list[str] = []
    difficulty: str = "medium"

class QuestionResponse(BaseModel):
    id: uuid.UUID
    content: str
    answer_hint: str | None = None
    job_title: str
    skills: list[str] | None = None
    difficulty: str
    source: str
    created_at: datetime
    model_config = {"from_attributes": True}

class QuestionBatchImport(BaseModel):
    questions: list[QuestionCreate]