import asyncio
import uuid
from app.tasks.celery_app import celery_app
from app.database import async_session
from app.models.question import Question
from app.services.dashscope import embed_batch
from sqlalchemy import select

@celery_app.task(name="embed_questions")
def embed_questions_task(question_ids: list[str]):
    return asyncio.run(_embed_questions_async(question_ids))

async def _embed_questions_async(question_ids: list[str]):
    async with async_session() as db:
        result = await db.execute(
            select(Question).where(Question.id.in_([uuid.UUID(qid) for qid in question_ids]))
        )
        questions = result.scalars().all()
        # DashScope 批量限制最多 10 条，分批处理
        batch_size = 10
        for i in range(0, len(questions), batch_size):
            batch = questions[i:i + batch_size]
            texts = [q.content for q in batch]
            embeddings = await embed_batch(texts)
            for q, emb in zip(batch, embeddings):
                q.embedding = emb
        await db.commit()
    return {"embedded": len(questions)}