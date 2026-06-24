import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.question import Question
from app.schemas.question import QuestionCreate, QuestionResponse, QuestionBatchImport
from app.services.rag import search_questions
from app.tasks.question_tasks import embed_questions_task

router = APIRouter(prefix="/api/questions", tags=["questions"])

@router.get("", response_model=list[QuestionResponse])
async def list_questions(
    job_title: str | None = Query(None),
    difficulty: str | None = Query(None),
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Question)
    if job_title:
        stmt = stmt.where(Question.job_title == job_title)
    if difficulty:
        stmt = stmt.where(Question.difficulty == difficulty)
    stmt = stmt.offset(skip).limit(limit).order_by(Question.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("", response_model=QuestionResponse)
async def create_question(data: QuestionCreate, db: AsyncSession = Depends(get_db)):
    question = Question(
        content=data.content,
        answer_hint=data.answer_hint,
        job_title=data.job_title,
        skills=data.skills,
        difficulty=data.difficulty,
        source="manual",
    )
    db.add(question)
    await db.commit()
    await db.refresh(question)
    embed_questions_task.delay([str(question.id)])
    return question

@router.post("/batch")
async def batch_import(data: QuestionBatchImport, db: AsyncSession = Depends(get_db)):
    question_ids = []
    for q in data.questions:
        question = Question(
            content=q.content,
            answer_hint=q.answer_hint,
            job_title=q.job_title,
            skills=q.skills,
            difficulty=q.difficulty,
            source="manual",
        )
        db.add(question)
        await db.flush()
        question_ids.append(str(question.id))
    await db.commit()
    embed_questions_task.delay(question_ids)
    return {"imported": len(question_ids), "ids": question_ids}

@router.post("/re-embed")
async def re_embed_all(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Question.id))
    all_ids = [str(row[0]) for row in result]
    if all_ids:
        embed_questions_task.delay(all_ids)
    return {"queued": len(all_ids)}

@router.get("/search")
async def search_questions_api(
    q: str = Query(...),
    job_title: str | None = Query(None),
    difficulty: str | None = Query(None),
    top_k: int = 5,
    db: AsyncSession = Depends(get_db),
):
    return await search_questions(db, job_title=job_title, skill=q, difficulty=difficulty, top_k=top_k)