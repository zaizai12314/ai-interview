import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.interview import Interview
from app.models.resume import Resume
from app.schemas.interview import InterviewCreate, InterviewResponse, AnswerSubmit
from app.tasks.interview_tasks import agent_interview_step_task

router = APIRouter(prefix="/api/interview", tags=["interview"])

@router.post("/create", response_model=InterviewResponse)
async def create_interview(data: InterviewCreate, db: AsyncSession = Depends(get_db)):
    resume = await db.get(Resume, data.resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if not resume.skills:
        raise HTTPException(status_code=400, detail="Resume not parsed yet")

    interview = Interview(
        resume_id=data.resume_id,
        target_job=data.target_job,
        status="in_progress",
    )
    db.add(interview)
    await db.commit()
    await db.refresh(interview)

    agent_interview_step_task.delay(str(interview.id))
    return interview

@router.get("/{interview_id}")
async def get_interview_state(interview_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    interview = await db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404)

    import redis.asyncio as aioredis
    from app.config import settings
    import json
    r = aioredis.from_url(settings.redis_url)
    agent_data = await r.get(f"interview:{interview_id}")
    await r.aclose()

    agent_state = json.loads(agent_data) if agent_data else {}
    history = agent_state.get("history", [])

    # 提取最新一条评估结果（刚回答完的评分和反馈）
    latest_evaluation = None
    if history:
        last = history[-1]
        if last.get("answer"):
            # 最后一条已有回答 → 刚评估完（通常是面试结束时的最后一条）
            latest_evaluation = {
                "score": last.get("score", 0),
                "feedback": last.get("feedback", ""),
                "round": last.get("round", 0),
            }
        elif len(history) >= 2:
            # 倒数第二条有回答 → 这是刚评估完的（新题目已被追加到末尾）
            prev = history[-2]
            if prev.get("answer"):
                latest_evaluation = {
                    "score": prev.get("score", 0),
                    "feedback": prev.get("feedback", ""),
                    "round": prev.get("round", 0),
                }

    return {
        "id": str(interview.id),
        "status": interview.status,
        "target_job": interview.target_job,
        "total_rounds": interview.total_rounds,
        "history": interview.history or [],
        "current_question": history[-1].get("question") if history else None,
        "current_round": agent_state.get("current_round", 0),
        "evaluation": latest_evaluation,
    }

@router.post("/{interview_id}/answer")
async def submit_answer(interview_id: uuid.UUID, data: AnswerSubmit, db: AsyncSession = Depends(get_db)):
    interview = await db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404)
    if interview.status != "in_progress":
        raise HTTPException(status_code=400, detail="Interview already completed")

    agent_interview_step_task.delay(str(interview_id), data.answer)
    return {'status': 'processing', 'interview_id': str(interview_id)}

@router.get("/{interview_id}/report")
async def get_report(interview_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    interview = await db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404)
    if interview.status != "completed":
        raise HTTPException(status_code=400, detail="Interview not completed yet")
    return {
        "id": str(interview.id),
        "target_job": interview.target_job,
        "history": interview.history,
        "scores": interview.scores,
        "report": interview.report,
        "completed_at": str(interview.completed_at),
    }

@router.delete("/{interview_id}")
async def delete_interview(interview_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    interview = await db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404)
    await db.delete(interview)
    await db.commit()
    return {"status": "deleted"}

@router.get("/history/list")
async def list_history(skip: int = 0, limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Interview).order_by(Interview.created_at.desc()).offset(skip).limit(limit)
    )
    interviews = result.scalars().all()
    return [{"id": str(i.id), "target_job": i.target_job, "status": i.status, "total_rounds": i.total_rounds, "created_at": str(i.created_at)} for i in interviews]
