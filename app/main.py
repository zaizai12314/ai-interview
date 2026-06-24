from fastapi import FastAPI

from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from sqlalchemy import select, func

app = FastAPI(title="AI Interview", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def seed_questions_on_startup():
    from app.database import async_session
    from app.models.question import Question
    from app.tasks.question_tasks import embed_questions_task

    seed_path = "seed_data/questions.json"
    if not os.path.exists(seed_path):
        return

    async with async_session() as db:
        count = await db.scalar(select(func.count()).select_from(Question))
        if count > 0:
            return

        with open(seed_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        question_ids = []
        for q in data["questions"]:
            question = Question(
                content=q["content"],
                answer_hint=q["answer_hint"],
                job_title=q["job_title"],
                skills=q["skills"],
                difficulty=q["difficulty"],
                source="system",
            )
            db.add(question)
            await db.flush()
            question_ids.append(str(question.id))

        await db.commit()

    if question_ids:
        embed_questions_task.delay(question_ids)
        print(f"Seeded {len(question_ids)} questions, embedding queued.")

from app.routes.resume_api import router as resume_router
from app.routes.interview_api import router as interview_router
app.include_router(resume_router)
app.include_router(interview_router)




@app.get("/api/health")
async def health():
    return {"status": "ok"}

app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
