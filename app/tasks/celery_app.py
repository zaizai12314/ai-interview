from celery import Celery
from app.config import settings

celery_app = Celery(
    "ai_interview",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

import app.tasks.resume_tasks  # noqa: F401
import app.tasks.interview_tasks  # noqa: F401
import app.tasks.question_tasks  # noqa: F401

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
