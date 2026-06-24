import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from app.database import Base

class Question(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    answer_hint: Mapped[str | None] = mapped_column(Text)
    job_title: Mapped[str] = mapped_column(String(128), nullable=False)
    skills: Mapped[dict | None] = mapped_column(JSONB)
    difficulty: Mapped[str] = mapped_column(String(16), default="medium")
    embedding = mapped_column(Vector(1024))
    source: Mapped[str] = mapped_column(String(32), default="manual")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
