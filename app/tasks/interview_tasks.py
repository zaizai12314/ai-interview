import json
import uuid
from datetime import datetime
from app.tasks.celery_app import celery_app
from app.config import settings
import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models.interview import Interview
from app.models.resume import Resume
from app.agent.interviewer import InterviewerAgent
from app.agent.evaluator import EvaluatorAgent
from app.services.rag import search_questions_sync


def _retrieve_questions(
    resume_skills: list[str],
    job_title: str,
    current_round: int,
    history_length: int,
) -> list[dict]:
    """RAG 检索题库中与当前技能相关的问题"""
    if not resume_skills:
        return []
    # 根据轮次轮询选择技能，确保覆盖多个方向
    skill_idx = (current_round - 1) % len(resume_skills) if current_round > 0 else 0
    skill = resume_skills[skill_idx]
    return search_questions_sync(
        job_title=job_title,
        skill=skill,
        top_k=3,
        similarity_threshold=0.5,
    )


@celery_app.task(name="agent_interview_step")
def agent_interview_step_task(interview_id: str, answer: str | None = None):
    engine = create_engine(settings.database_url_sync, echo=False)
    SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
    r = redis.from_url(settings.redis_url)

    with SessionLocal() as db:
        interview = db.get(Interview, uuid.UUID(interview_id))
        resume = db.get(Resume, interview.resume_id)
        redis_key = f"interview:{interview_id}"
        agent_bytes = r.get(redis_key)

        # ── 首次调用：生成第一题 ──────────────────────────────
        if not agent_bytes and answer is None:
            agent = InterviewerAgent(
                skills=resume.skills or [],
                job_title=interview.target_job,
                max_rounds=10,
            )
            retrieved = _retrieve_questions(
                resume.skills or [], interview.target_job, 1, 0
            )
            result = agent.start_interview_sync(retrieved_questions=retrieved)

            interview.history = agent.history
            interview.total_rounds = agent.current_round
            db.commit()

            r.setex(redis_key, 3600, json.dumps(agent.to_dict(), default=str))
            r.close()
            return {
                "action": "ask_question",
                "content": result.get("content", ""),
                "round": 1,
                "progress": 0.1,
            }

        # ── 后续调用：处理回答 ────────────────────────────────
        if agent_bytes and answer is not None:
            agent = InterviewerAgent.from_dict(json.loads(agent_bytes))

            # 评估回答
            last_q = agent.history[-1]["question"] if agent.history else ""
            evaluator = EvaluatorAgent()
            evaluation = evaluator.evaluate_sync(last_q, answer)

            # RAG 检索下一题参考
            cr = agent.current_round
            retrieved = _retrieve_questions(
                agent.skills, agent.job_title, cr + 1, len(agent.history)
            )

            # 处理回答，生成下一题或结束
            result = agent.process_answer_sync(answer, evaluation,
                                                retrieved_questions=retrieved)

            # 更新数据库
            interview.history = agent.history
            interview.total_rounds = cr

            if result.get("action") == "finish" or cr >= agent.max_rounds:
                interview.status = "completed"
                interview.completed_at = datetime.utcnow()
                interview.report = agent.generate_report_sync()

            db.commit()

            # 保存状态到 Redis（如果面试结束则不需要再轮询了）
            if interview.status != "completed":
                r.setex(redis_key, 3600, json.dumps(agent.to_dict(), default=str))
            else:
                r.delete(redis_key)
            r.close()

            return {
                "action": result.get("action", "ask_question"),
                "content": result.get("content", ""),
                "round": cr,
                "progress": min(cr / 10, 1.0),
            }

        # ── 异常状态 ──────────────────────────────────────────
        r.close()
        return {"action": "error", "content": "Invalid state"}
