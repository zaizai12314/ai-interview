import uuid
import os
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.resume import Resume
from app.tasks.resume_tasks import _extract_text
from app.schemas.resume import ResumeResponse, JobMatch
from app.config import settings
import json as _json

router = APIRouter(prefix="/api/resume", tags=["resume"])


def _parse_resume_sync(raw_text: str) -> dict:
    import asyncio as _asyncio
    from app.services.deepseek import parse_resume as _deepseek_parse
    parsed = _asyncio.run(_deepseek_parse(raw_text))
    if isinstance(parsed, str):
        parsed = _json.loads(parsed)
    return parsed


async def _process_resume_inline(resume: Resume, file_path: str, db: AsyncSession):
    import redis.asyncio as aioredis
    from app.services.deepseek import match_jobs as _deepseek_match
    raw_text = _extract_text(file_path)
    loop = __import__("asyncio").get_event_loop()
    parsed = await loop.run_in_executor(None, _parse_resume_sync, raw_text)
    skills = parsed.get("skills", [])
    resume.raw_text = raw_text
    resume.skills = skills
    resume.experience = parsed.get("experience", [])
    resume.education = parsed.get("education", {})
    resume.parsed_at = datetime.utcnow()
    await db.commit()
    await db.refresh(resume)
    try:
        jobs = await _deepseek_match(skills)
        if isinstance(jobs, str):
            jobs = _json.loads(jobs)
        r = aioredis.from_url(settings.redis_url)
        await r.set(f"jobs:{resume.id}", _json.dumps(jobs), ex=3600)
        await r.aclose()
    except Exception:
        pass


def _find_upload_file(resume: Resume) -> str | None:
    """Find the uploaded file for a resume by matching filename suffix."""
    upload_dir = settings.upload_dir
    if not os.path.isdir(upload_dir):
        return None
    for fname in os.listdir(upload_dir):
        if fname.endswith("_" + resume.filename):
            return os.path.join(upload_dir, fname)
    return None


@router.post("/upload")
async def upload_resume(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    os.makedirs(settings.upload_dir, exist_ok=True)
    file_path = os.path.join(settings.upload_dir, f"{uuid.uuid4()}_{file.filename}")
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    resume = Resume(filename=file.filename)
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    try:
        from app.tasks.resume_tasks import parse_resume_task
        parse_resume_task.delay(str(resume.id), file_path)
    except Exception:
        await _process_resume_inline(resume, file_path, db)
    return {"id": str(resume.id), "filename": file.filename, "status": "pending"}


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(resume_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    resume = await db.get(Resume, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume


@router.get("/{resume_id}/status")
async def get_resume_status(resume_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    resume = await db.get(Resume, resume_id)
    if not resume:
        raise HTTPException(status_code=404)
    if resume.parsed_at:
        return {"status": "parsed", "resume_id": str(resume_id)}

    # Auto-retry: if resume is not yet parsed, try inline processing
    file_path = _find_upload_file(resume)
    if file_path:
        try:
            await _process_resume_inline(resume, file_path, db)
            return {"status": "parsed", "resume_id": str(resume_id)}
        except Exception as e:
            return {"status": "error", "resume_id": str(resume_id), "detail": str(e)}

    return {"status": "pending", "resume_id": str(resume_id)}


@router.get("/{resume_id}/jobs", response_model=list[JobMatch])
async def get_job_matches(resume_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    import redis.asyncio as aioredis
    resume = await db.get(Resume, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if not resume.skills:
        return []  # 简历尚未解析出技能标签，返回空列表而非 404
    r = aioredis.from_url(settings.redis_url)
    cached = await r.get(f"jobs:{resume_id}")
    if cached:
        await r.aclose()
        return _json.loads(cached)
    from app.services.deepseek import match_jobs
    try:
        result = await match_jobs(resume.skills)
        if isinstance(result, str):
            result = _json.loads(result)
        await r.set(f"jobs:{resume_id}", _json.dumps(result), ex=3600)
        await r.aclose()
        return result
    except Exception:
        await r.aclose()
        return []  # 岗位匹配失败时返回空列表，前端可自行重试