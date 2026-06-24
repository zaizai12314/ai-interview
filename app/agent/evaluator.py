import json
from app.services.deepseek import chat_completion, chat_completion_sync


class EvaluatorAgent:
    """评分智能体：专注评估面试回答质量"""

    SYSTEM_PROMPT = (
        "你是一个严格的技术面试官。请按以下标准给候选人的回答评分：\n"
        "  - 0-20: 完全无关或空白回答\n"
        "  - 21-40: 回答太简短(少于20字)或严重偏离要点\n"
        "  - 41-60: 部分正确但不够完整，或答非所问\n"
        "  - 61-80: 基本正确但缺少深入分析或细节\n"
        "  - 81-90: 回答正确且有较好的解释\n"
        "  - 91-100: 回答全面、深入、有见解\n"
        "要求：\n"
        "  1. 对非常简短的回答(如只有几个字)直接给低分\n"
        "  2. 技术问题回答错误或不准确必须扣分\n"
        "  3. 保持严格标准，不要随意给高分\n"
        "以 JSON 格式返回: score, feedback(中文1-2句), is_correct(正确/部分正确/错误)"
    )

    def evaluate_sync(self, question: str, answer: str) -> dict:
        """同步评分（供 Celery 使用）"""
        msgs = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"题目: {question}\n候选人回答: {answer}"},
        ]
        r = chat_completion_sync(msgs, temperature=0.3)
        return self._parse(r)

    async def evaluate(self, question: str, answer: str) -> dict:
        """异步评分（供 API 直接调用）"""
        msgs = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"题目: {question}\n候选人回答: {answer}"},
        ]
        r = await chat_completion(msgs, temperature=0.3)
        return self._parse(r)

    def _parse(self, raw: str | None) -> dict:
        """解析 LLM 返回的 JSON，兼容空值和格式异常"""
        if not raw:
            return {"score": 0, "feedback": "评估失败，请重试", "is_correct": "错误"}
        # 兼容 markdown ```json 包裹
        if "```" in raw:
            import re
            m = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
            if m:
                raw = m.group(1).strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"score": 50, "feedback": "解析评估结果失败", "is_correct": "部分正确"}
