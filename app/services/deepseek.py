from openai import AsyncOpenAI
from app.config import settings

client = AsyncOpenAI(
    api_key=settings.deepseek_api_key,
    base_url=settings.deepseek_base_url,
)

# Sync client for Celery tasks (avoids event loop issues)
from openai import OpenAI as SyncOpenAI
sync_client = SyncOpenAI(
    api_key=settings.deepseek_api_key,
    base_url=settings.deepseek_base_url,
)

def chat_completion_sync(messages: list[dict], temperature: float = 0.7, max_tokens: int = 2048) -> str:
    r = sync_client.chat.completions.create(
        model=settings.deepseek_model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return r.choices[0].message.content

async def chat_completion(messages: list[dict], temperature: float = 0.7, max_tokens: int = 2048) -> str:
    """通用 LLM 对话"""
    response = await client.chat.completions.create(
        model=settings.deepseek_model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    content = response.choices[0].message.content
    return content or ""

async def parse_resume(raw_text: str) -> dict:
    """解析简历文本，提取结构化信息"""
    import json
    import re
    messages = [
        {"role": "system", "content": "你是一个专业的简历解析器。从简历文本中提取: skills(技能列表), experience(工作经历数组), education(教育背景)。以 JSON 格式返回，不要包含其他内容。"},
        {"role": "user", "content": raw_text},
    ]
    result = await chat_completion(messages, temperature=0.1)
    if not result:
        return {"skills": [], "experience": [], "education": []}
    # 提取 JSON 块（兼容 LLM 返回 markdown 包裹）
    if "```" in result:
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", result)
        if m:
            result = m.group(1).strip()
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return {"skills": [], "experience": [], "education": []}

async def match_jobs(skills: list[str]) -> list[dict]:
    """根据技能标签推荐匹配岗位"""
    import json
    import re
    skills_str = ", ".join(skills)
    messages = [
        {"role": "system", "content": "你是一个职业顾问。根据候选人的技能，推荐 3-5 个最匹配的技术岗位。以 JSON 数组返回，每个岗位包含: title, match_score(0-100), reason。"},
        {"role": "user", "content": f"技能: {skills_str}"},
    ]
    result = await chat_completion(messages, temperature=0.5)
    if not result:
        return []
    if "```" in result:
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", result)
        if m:
            result = m.group(1).strip()
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return []

async def evaluate_answer(question: str, reference_answer: str, user_answer: str) -> dict:
    """评估回答质量，打分+反馈"""
    import json
    import re
    messages = [
        {"role": "system", "content": "你是严格的面试官。评估候选人的回答并给出: score(0-100整数), feedback(1-2句中肯点评,中文), is_correct(正确/部分正确/错误)。以 JSON 格式返回。"},
        {"role": "user", "content": f"题目: {question}\n参考答案要点: {reference_answer}\n候选人回答: {user_answer}"},
    ]
    result = await chat_completion(messages, temperature=0.3)
    if not result:
        return {"score": 0, "feedback": "评估失败，请重试", "is_correct": "错误"}
    if "```" in result:
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", result)
        if m:
            result = m.group(1).strip()
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return {"score": 0, "feedback": "解析评估结果失败", "is_correct": "错误"}

async def generate_report(interview_history: list[dict], target_job: str) -> str:
    """生成面试综合报告"""
    history_text = "\n".join([
        f"第{r['round']}轮: {r['question']}\n回答: {r['answer']}\n得分: {r['score']}"
        for r in interview_history
    ])
    messages = [
        {"role": "system", "content": f"你是面试评估专家。根据{target_job}岗位的面试记录，生成一份结构化的面试报告，包含: 总体评价、优势、待改进项、学习建议。用中文输出 Markdown 格式。"},
        {"role": "user", "content": history_text},
    ]
    return await chat_completion(messages, temperature=0.5, max_tokens=4096)
