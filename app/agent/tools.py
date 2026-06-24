from sqlalchemy.ext.asyncio import AsyncSession
from app.services.rag import search_questions
from app.services.deepseek import chat_completion
from app.agent.evaluator import EvaluatorAgent

async def tool_search_questions(
    db: AsyncSession,
    job_title: str,
    skill: str,
    difficulty: str = "medium",
    top_k: int = 5,
) -> list[dict]:
    """Agent 工具: RAG 检索题库"""
    return await search_questions(db, job_title=job_title, skill=skill, difficulty=difficulty, top_k=top_k)

async def tool_generate_question(
    job_title: str,
    skill: str,
    difficulty: str,
    previous_context: str = "",
) -> str:
    """Agent 工具: LLM 动态生成面试题"""
    messages = [
        {"role": "system", "content": f"你是{job_title}岗位的技术面试官。为考察{skill}技能，出一道{difficulty}难度的面试题。只输出题目内容，不要解释。"},
    ]
    if previous_context:
        messages.append({"role": "user", "content": f"前一轮面试背景: {previous_context}\n请出一道新题。"})
    else:
        messages.append({"role": "user", "content": "请出一道面试题。"})
    return await chat_completion(messages, temperature=0.8)

async def tool_evaluate_answer(question: str, answer: str, reference_hint: str = "") -> dict:
    """Agent 工具: 评分"""
    evaluator = EvaluatorAgent()
    return await evaluator.evaluate(question, answer)
