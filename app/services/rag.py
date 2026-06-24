from sqlalchemy import text, create_engine
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.dashscope import embed_text, embed_text_sync
from app.config import settings


async def search_questions(
    db: AsyncSession,
    job_title: str | None = None,
    skill: str | None = None,
    difficulty: str | None = None,
    top_k: int = 5,
) -> list[dict]:
    """语义检索题库，基于 pgvector 余弦相似度"""
    query_text = f"{job_title or ''} {skill or ''}".strip()
    if not query_text:
        return []

    embedding = await embed_text(query_text)
    return _search(embedding, job_title, difficulty, top_k)


def search_questions_sync(
    job_title: str | None = None,
    skill: str | None = None,
    difficulty: str | None = None,
    top_k: int = 3,
    similarity_threshold: float = 0.7,
) -> list[dict]:
    """同步语义检索（供 Celery Worker 使用）"""
    query_text = f"{job_title or ''} {skill or ''}".strip()
    if not query_text:
        return []

    embedding = embed_text_sync(query_text)
    # 优先按 job_title 精确匹配，若无结果则放宽到所有题目
    results = _search(embedding, job_title, difficulty, top_k)
    if not results:
        results = _search(embedding, None, difficulty, top_k)
    return [r for r in results if r["similarity"] >= similarity_threshold]


def _search(
    embedding: list[float],
    job_title: str | None,
    difficulty: str | None,
    top_k: int,
) -> list[dict]:
    """执行 pgvector 检索（同步，供内部调用）"""
    engine = create_engine(settings.database_url_sync, echo=False)
    import json
    embedding_json = json.dumps(embedding)
    sql = text("""
        SELECT id, content, answer_hint, job_title, skills, difficulty, source,
               1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
        FROM questions
        WHERE (:job_title IS NULL OR job_title = :job_filter)
          AND (:difficulty IS NULL OR difficulty = :diff_filter)
        ORDER BY embedding <=> CAST(:embedding AS vector)
        LIMIT :top_k
    """)
    with Session(engine) as db:
        result = db.execute(sql, {
            "embedding": embedding_json,
            "job_filter": job_title,
            "job_title": job_title,
            "difficulty": difficulty,
            "diff_filter": difficulty,
            "top_k": top_k,
        })
        return [
            {
                "id": str(row.id),
                "content": row.content,
                "answer_hint": row.answer_hint,
                "job_title": row.job_title,
                "skills": row.skills,
                "difficulty": row.difficulty,
                "source": row.source,
                "similarity": round(float(row.similarity), 4) if row.similarity is not None else 0.0,
            }
            for row in result
        ]
