# AI 模拟面试系统

基于 FastAPI + Vue 3 + DeepSeek 的 AI 模拟面试平台，支持简历解析、智能出题、回答评分和面试报告生成。

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | FastAPI + SQLAlchemy async + PostgreSQL / pgvector |
| 前端 | Vue 3 + Vite + Tailwind CSS |
| 异步任务 | Celery + Redis |
| LLM | DeepSeek API（出题、评分、简历解析、岗位匹配） |
| Embedding | DashScope text-embedding-v3（题库向量化） |
| 容器化 | Docker Compose |

## 快速开始

### 1. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`：

```ini
DEEPSEEK_API_KEY=sk-your-deepseek-api-key
DASHSCOPE_API_KEY=sk-your-dashscope-api-key
```

### 2. 启动

```bash
docker compose up -d
```

首次启动会自动导入种子题目并生成向量嵌入。

### 3. 访问

- **前端页面**：http://localhost:8000
- **API 健康检查**：http://localhost:8000/api/health

## 使用流程

```
上传简历 → 解析简历（DeepSeek）→ 岗位匹配 → 开始面试
                                            ↓
                RAG 检索题库 → 参考出题 → 用户回答 → 评分 → 下一题
                                            ↓
                                       面试报告
```

- **简历格式**：支持 `.pdf`、`.docx`、`.txt`
- **面试轮次**：默认 10 轮，LLM 会根据回答质量动态调整

## 项目结构

```
├── app/
│   ├── agent/              # 智能体
│   │   ├── interviewer.py  # 面试官 Agent（出题、决策）
│   │   ├── evaluator.py    # 评分 Agent（评估回答）
│   │   └── prompts.py      # 系统提示词
│   ├── routes/             # API 路由
│   │   ├── interview_api.py
│   │   └── resume_api.py
│   ├── services/           # 外部服务
│   │   ├── deepseek.py     # DeepSeek LLM 调用
│   │   ├── dashscope.py    # DashScope 向量化
│   │   └── rag.py          # pgvector 语义检索
│   ├── tasks/              # Celery 异步任务
│   │   ├── interview_tasks.py
│   │   ├── resume_tasks.py
│   │   └── question_tasks.py
│   ├── models/             # SQLAlchemy 模型
│   ├── schemas/            # Pydantic 模型
│   └── main.py             # FastAPI 入口
├── frontend/
│   └── src/
│       ├── views/          # 页面组件
│       ├── components/     # UI 组件
│       └── api/            # API 客户端
├── seed_data/              # 种子题库
├── docker-compose.yml
└── requirements.txt
```

## 环境变量

| 变量 | 说明 | 默认值 |
|---|---|---|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | — |
| `DEEPSEEK_BASE_URL` | DeepSeek API 地址 | `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | DeepSeek 模型 | `deepseek-chat` |
| `DASHSCOPE_API_KEY` | 阿里云 DashScope 密钥 | — |
| `DASHSCOPE_EMBEDDING_MODEL` | 向量模型 | `text-embedding-v3` |
| `DATABASE_URL` | PostgreSQL 连接串 | `postgresql+asyncpg://postgres:postgres@localhost:5432/ai_interview` |
| `REDIS_URL` | Redis 连接串 | `redis://localhost:6379/0` |

## 关键特性

- **RAG 增强出题**：出题前从题库中检索语义相似题目，作为参考注入 LLM 上下文，提高题目质量
- **严格评分**：基于严格标准的评分 Agent，对简短或无关回答自动给低分
- **自适应面试**：LLM 根据回答质量动态调整难度和考察方向
- **Resume 解析**：自动提取技能、经历、教育信息并匹配推荐岗位
