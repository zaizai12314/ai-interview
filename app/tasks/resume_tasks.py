import json
import uuid
from datetime import datetime
from app.tasks.celery_app import celery_app
from app.config import settings

def _extract_text(file_path: str) -> str:
    import os
    ext = os.path.splitext(file_path)[1].lower()
    if ext in (".docx", ".doc"):
        from docx import Document
        from docx.oxml.ns import qn
        doc = Document(file_path)
        # python-docx 的 doc.paragraphs 不遍历文本框(w:txbxContent)内的段落
        # 从 XML 层取所有 w:p 元素，包含文本框中的内容
        nsmap = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        all_paras = doc.element.body.findall(".//w:p", nsmap)
        lines = []
        for p in all_paras:
            t_els = p.findall(".//w:t", nsmap)
            text = "".join(t.text or "" for t in t_els)
            if text.strip():
                lines.append(text.strip())
        return chr(10).join(lines) if lines else ""
    elif ext == ".pdf":
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        lines = []
        for page in doc:
            text = page.get_text().strip()
            if text:
                lines.append(text)
        doc.close()
        return chr(10).join(lines) if lines else ""
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

@celery_app.task(bind=True, name='parse_resume')
def parse_resume_task(self, resume_id: str, file_path: str):
    import asyncio as _asyncio
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker, Session
    import redis
    from app.models.resume import Resume
    from app.services.deepseek import parse_resume as deepseek_parse, match_jobs as deepseek_match

    engine = create_engine(settings.database_url_sync, echo=False)
    SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
    r = redis.from_url(settings.redis_url)

    raw_text = _extract_text(file_path)

    parsed = _asyncio.run(deepseek_parse(raw_text))
    if isinstance(parsed, str):
        parsed = json.loads(parsed)

    skills = parsed.get('skills', [])

    with SessionLocal() as db:
        resume = db.get(Resume, uuid.UUID(resume_id))
        if resume:
            resume.raw_text = raw_text
            resume.skills = skills
            resume.experience = parsed.get('experience', [])
            resume.education = parsed.get('education', {})
            resume.parsed_at = datetime.utcnow()
            db.commit()

    jobs = _asyncio.run(deepseek_match(skills))
    if isinstance(jobs, str):
        jobs = json.loads(jobs)

    r.set(f'jobs:{resume_id}', json.dumps(jobs), ex=3600)
    r.close()

    return {'resume_id': resume_id, 'jobs': jobs}
