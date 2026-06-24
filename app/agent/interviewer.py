import json
from app.services.deepseek import chat_completion_sync
from app.agent.prompts import INTERVIEWER_SYSTEM_PROMPT, INTERVIEW_START_PROMPT


class InterviewerAgent:
    def __init__(self, skills: list[str], job_title: str, max_rounds: int = 10):
        self.skills = skills
        self.job_title = job_title
        self.max_rounds = max_rounds
        self.history: list[dict] = []
        self.current_round = 0
        self.current_skill_index = 0
        self.messages = [
            {"role": "system", "content": INTERVIEWER_SYSTEM_PROMPT},
        ]

    # ── Redis 序列化 ──────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "skills": self.skills,
            "job_title": self.job_title,
            "max_rounds": self.max_rounds,
            "history": self.history,
            "current_round": self.current_round,
            "current_skill_index": self.current_skill_index,
            "messages": self.messages,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "InterviewerAgent":
        agent = cls(
            skills=data.get("skills", []),
            job_title=data.get("job_title", ""),
            max_rounds=data.get("max_rounds", 10),
        )
        agent.history = data.get("history", [])
        agent.current_round = data.get("current_round", 0)
        agent.current_skill_index = data.get("current_skill_index", 0)
        agent.messages = data.get("messages", [
            {"role": "system", "content": INTERVIEWER_SYSTEM_PROMPT},
        ])
        return agent

    # ── 公开方法 ─────────────────────────────────────────────

    def get_start_prompt(self) -> str:
        return INTERVIEW_START_PROMPT.format(
            skills=", ".join(self.skills),
            job_title=self.job_title,
            max_rounds=self.max_rounds,
        )

    def start_interview_sync(self, retrieved_questions: list[dict] | None = None) -> dict:
        prompt = self.get_start_prompt()
        self.messages.append({"role": "user", "content": prompt})
        self._inject_rag_context(retrieved_questions)
        response = chat_completion_sync(self.messages, temperature=0.8)
        self.messages.append({"role": "assistant", "content": response})
        self.current_round = 1
        result = self._parse_response(response)
        self.history.append({
            "round": 1,
            "question": result.get("content", ""),
            "answer": "",
            "score": 0,
            "feedback": "",
        })
        return result

    def process_answer_sync(self, answer: str, evaluation: dict,
                            retrieved_questions: list[dict] | None = None) -> dict:
        feedback_msg = (
            f"score:{evaluation.get('score', 0)}/100, "
            f"correct:{evaluation.get('is_correct', 'partial')}, "
            f"feedback:{evaluation.get('feedback', '')}"
        )
        self.messages.append({"role": "user", "content": feedback_msg})

        if self.history:
            self.history[-1]["answer"] = answer
            self.history[-1]["score"] = evaluation.get("score")
            self.history[-1]["feedback"] = evaluation.get("feedback")

        if self.current_round >= self.max_rounds:
            return self._finish()

        self.current_round += 1
        self._inject_rag_context(retrieved_questions)
        response = chat_completion_sync(self.messages, temperature=0.8)
        self.messages.append({"role": "assistant", "content": response})

        parsed = self._parse_response(response)
        c = parsed.get("content")
        if not isinstance(c, str) or not c.strip():
            response = chat_completion_sync(self.messages, temperature=0.9)
            self.messages.append({"role": "assistant", "content": response})
            parsed = self._parse_response(response)

        act = parsed.get("action")
        if act == "ask_question":
            self.history.append({
                "round": self.current_round,
                "question": parsed.get("content", ""),
                "answer": "",
                "score": 0,
                "feedback": "",
            })
        return parsed

    def generate_report_sync(self) -> str:
        """生成面试总结报告（同步版，供 Celery 使用）"""
        parts = []
        for h in self.history:
            parts.append(
                f"R{h['round']}: Q:{h['question']} A:{h['answer']} Score:{h['score']}"
            )
        text = "\n".join(parts)
        msgs = [
            {"role": "system",
             "content": f"Generate interview report for {self.job_title}. Include: overall, strengths, improvements, suggestions. Chinese Markdown."},
            {"role": "user", "content": text},
        ]
        return chat_completion_sync(msgs, temperature=0.5, max_tokens=4096)

    # ── RAG 上下文注入 ────────────────────────────────────────

    def _inject_rag_context(self, retrieved_questions: list[dict] | None):
        """将检索到的题库题目注入到 messages 中（紧跟 system prompt 之后）"""
        if not retrieved_questions:
            return
        lines = ["来自题库的相关面试题（供参考，可直接使用或改编）："]
        for i, q in enumerate(retrieved_questions, 1):
            diff = q.get("difficulty", "unknown")
            sim = q.get("similarity", 0)
            lines.append(f"{i}. {q['content']} (难度: {diff}, 相似度: {sim})")
        # 插在 system prompt 之后、第一条 user 消息之前
        self.messages.insert(1, {"role": "system", "content": "\n".join(lines)})

    # ── 内部方法 ─────────────────────────────────────────────

    def _parse_response(self, response):
        start = response.find("{")
        end = response.rfind("}")
        if start != -1 and end > start:
            try:
                result = json.loads(response[start:end + 1])
                content = result.get("content")
                if isinstance(content, str) and content.strip():
                    return result
                # content 非字符串（如嵌套对象）或为空 → 用原始响应作为内容
                return {"action": result.get("action", "ask_question"), "content": response.strip()}
            except json.JSONDecodeError:
                pass
        return {"action": "ask_question", "content": response.strip()}

    def _finish(self) -> dict:
        return {"action": "finish", "content": "面试已结束，正在生成报告..."}

    def get_history(self) -> list[dict]:
        return self.history
