# AI Interview 智能模拟面试系统 — 设计文档

> 日期: 2026-06-23 | 状态: 设计中

## 1. 项目概述

面向求职场景的 AI 模拟面试系统，围绕"简历解析 → 岗位匹配 → **Agent 智能面试**（RAG检索+动态出题+追问）→ AI 评分 → 面试报告"构建完整闭环。系统定位为**可演示原型**，采用 FastAPI + Vue 3 + Celery 异步架构。

**核心亮点**: 面试官 Agent 不仅是出题器，而是具备决策能力的智能体——根据候选人每轮回答，动态决定：追问细节 / 切换方向 / 调整难度 / 结束面试。

## 2. 技术栈

**后端**
- Python 3.12 + FastAPI
- Celery（异步任务队列）
- SQLAlchemy 2.0（ORM）+ Alembic（数据库迁移）

**数据层**
- PostgreSQL 16 + pgvector（向量存储与语义检索）
- Redis 7（会话缓存 + Celery broker）

**AI 服务**
- DeepSeek API（简历解析、岗位匹配、Agent 决策、评分、报告生成）
- DashScope Embedding（题目向量化）

**Agent 框架**
- 面试官 Agent：基于 LLM 的工具调用（Function Calling）模式
- Agent 工具集：RAG 检索、题目生成、追问判断、难度调节

**前端**
- Vue 3 (Composition API) + Vite + Vue Router + Tailwind CSS

**部署**
- Docker Compose（FastAPI + PostgreSQL + Redis + Celery Worker）

## 3. 系统架构

```
┌──────────────────────────────────────────────┐
│            Vue 3 SPA (Vite)                  │
│   上传简历 · 岗位选择 · 面试 · 报告 · 题库     │
└────────────────────┬─────────────────────────┘
                     │ REST API
┌────────────────────▼─────────────────────────┐
│              FastAPI 应用 (纯 API)             │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ 简历 API │ │ 面试 API │ │  题库 API     │  │
│  └────┬─────┘ └────┬─────┘ └──────┬───────┘  │
│       │             │               │         │
│  ┌────▼─────────────▼───────────────▼───────┐ │
│  │          Celery 任务队列                  │ │
│  │  简历解析 · 岗位匹配 · Agent面试 · 评分   │ │
│  └────────────────────┬────────────────────┘ │
└───────────────────────┼──────────────────────┘
                        │
┌───────┬───────────────┼───────────────┬──────┐
│Postgre│   Redis       │   DeepSeek    │Dash  │
│+pgvec │   缓存+队列    │   API         │Scope │
└───────┴───────────────┴───────────────┴──────┘
```

## 4. Agent 设计（核心）

### 4.1 面试官 Agent 职责

```
                    ┌─────────────────────┐
                    │   面试官 Agent       │
                    │  (LLM + 工具调用)    │
                    └──────────┬──────────┘
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
   │ RAG 检索工具  │   │ 出题工具      │   │ 评分工具      │
   │ search_      │   │ generate_    │   │ evaluate_    │
   │ questions()  │   │ question()   │   │ answer()     │
   └──────────────┘   └──────────────┘   └──────────────┘
```

### 4.2 Agent 决策循环

```
面试开始
  │
  ▼
Agent 规划首题 ──→ 调用 RAG 检索 + LLM 出题 ──→ 展示题目
  │                                                  │
  │                                         用户提交回答
  │                                                  │
  │                                         调用评分工具
  │                                                  │
  │                                         反馈给用户
  │                                                  │
  ▼                                                  │
Agent 决策: ◀─────────────────────────────────────────┘
  ├── 回答充分 → 切换下一个技能考察方向
  ├── 回答不足 → 追问细节（深挖同一知识点）
  ├── 回答太差 → 降低难度，换基础题
  ├── 回答优秀 → 提高难度，挑战进阶题
  └── 轮次已满 → 结束面试，触发报告生成
```

### 4.3 Agent 工具定义

| 工具名 | 功能 | 输入参数 |
|--------|------|---------|
| search_questions | RAG 语义检索题库 | job_title, skill, difficulty, top_k |
| generate_question | LLM 动态生成面试题 | job_title, skill, difficulty, context (上轮回答摘要) |
| evaluate_answer | 评分 + 反馈 | question, answer, reference_answer |
| finish_interview | 结束面试 | reason, summary |

### 4.4 Agent 状态机

```
IDLE → PLANNING → QUESTIONING → WAITING_ANSWER
                                    │
                              SCORING ←┘
                                    │
                    ┌───────────────┤
                    ▼               ▼
              PLANNING          FINISHED
              (下一轮)          (生成报告)
```

## 5. 数据流

### 5.1 完整面试闭环

```
1. 上传简历 PDF/Word
      │
2. Celery: DeepSeek 解析简历 → 提取技能/经验
      │
3. Celery: DeepSeek 岗位匹配 → 推荐岗位列表
      │
4. 用户选择目标岗位
      │
5. 【Agent 接管】创建面试会话，初始化 Agent 上下文
      │
6. Agent 循环（每轮）：
   ├── RAG 检索 + LLM 出题 → 展示题目
   ├── 用户回答
   ├── Celery: 评分 + 反馈
   └── Agent 决策: 追问 / 切换方向 / 结束
      │
7. 面试结束 → Celery: DeepSeek 综合报告
      │
8. 面试报告页（总分、逐题点评、改进建议）
```

### 5.2 Redis 会话结构

```
interview:{session_id}
  ├── status: "in_progress" | "completed"
  ├── resume_id
  ├── target_job
  ├── skills_to_assess: ["Python","System Design","DB"]
  ├── agent_state:
  │   ├── current_skill_index: 1
  │   ├── current_round: 3
  │   ├── max_rounds: 10
  │   └── strategy: "deepen" | "switch" | "ease" | "challenge"
  ├── history:
  │   └── [{"round":1,"question":"...","answer":"...","score":85,"feedback":"..."}]
  └── scores: [{"question_id","score","feedback"},...]
```

## 6. 数据库模型

### 6.1 resumes（简历表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | |
| filename | VARCHAR(255) | 原始文件名 |
| raw_text | TEXT | 解析后原始文本 |
| skills | JSONB | ["Python","FastAPI"] |
| experience | JSONB | [{"company":"","role":"","years":""}] |
| education | JSONB | {"degree":"","school":"","major":""} |
| parsed_at | TIMESTAMP | |
| created_at | TIMESTAMP | |

### 6.2 interviews（面试记录表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | |
| resume_id | UUID FK → resumes | |
| target_job | VARCHAR(128) | 目标岗位 |
| status | VARCHAR(20) | in_progress / completed |
| total_rounds | INTEGER | 面试总轮数 |
| history | JSONB | 完整问答记录 |
| scores | JSONB | 逐题评分 |
| report | TEXT | DeepSeek 综合报告 |
| started_at | TIMESTAMP | |
| completed_at | TIMESTAMP | |
| created_at | TIMESTAMP | |

### 6.3 questions（题库表 + pgvector）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | |
| content | TEXT | 题目内容 |
| answer_hint | TEXT | 参考答案要点 |
| job_title | VARCHAR(128) | 适用岗位 |
| skills | JSONB | 考察技能标签 |
| difficulty | VARCHAR(16) | easy / medium / hard |
| embedding | VECTOR(1536) | DashScope 向量 |
| source | VARCHAR(32) | system / manual |
| created_at | TIMESTAMP | |

## 7. API 路由设计（纯 JSON）

### 7.1 简历

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/resume/upload | 上传简历 → 触发解析 + 匹配 |
| GET | /api/resume/{id} | 获取简历解析结果 |
| GET | /api/resume/{id}/status | 查询任务进度 |
| GET | /api/resume/{id}/jobs | 岗位匹配推荐 |

### 7.2 面试（Agent 驱动）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/interview/create | 选择岗位 → 创建会话 + Agent 初始化 |
| GET | /api/interview/{id} | 获取当前状态（题目/历史/进度） |
| POST | /api/interview/{id}/answer | 提交回答 → Agent 评分+决策 → 返回下一题或结束 |
| GET | /api/interview/{id}/report | 获取面试报告 |
| GET | /api/interview/history | 面试历史列表 |

### 7.3 题库

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/questions | 题库列表（分页） |
| POST | /api/questions | 手动添加题目 |
| POST | /api/questions/batch | 批量导入 |
| POST | /api/questions/re-embed | 重新向量化 |
| GET | /api/questions/search | 语义检索 |

## 8. Vue 前端

### 8.1 路由

| 路由 | 组件 | 说明 |
|------|------|------|
| / | HomePage | 首页 · 上传简历 |
| /resume/:id | ResumePage | 简历解析结果 · 岗位推荐 |
| /interview/:id | InterviewPage | **核心页** 一问一答面试 |
| /interview/:id/report | ReportPage | 面试报告 |
| /history | HistoryPage | 面试历史 |
| /questions | QuestionManagePage | 题库管理 |

### 8.2 面试页交互细节

```
InterviewPage 状态机:
  LOADING → 等待 Agent 出第一题
  QUESTIONING → 展示题目，等待用户输入
  SUBMITTING → 已提交答案，等待评分（轮询/SSE）
  FEEDBACK → 展示评分与反馈，Agent 决策指示
  NEXT → Agent 返回下一题 或 面试结束
  FINISHED → 跳转报告页
```

### 8.3 组件树

```
App.vue
├── HomePage.vue
│   └── FileUpload.vue
├── ResumePage.vue
│   ├── LoadingSpinner.vue
│   └── JobSelector.vue
├── InterviewPage.vue
│   ├── QuestionCard.vue       # 题目内容 + 输入区
│   ├── ScoreFeedback.vue      # 评分反馈弹窗
│   └── ProgressBar.vue        # 面试进度
├── ReportPage.vue
│   └── ScoreChart.vue         # 评分雷达图
├── HistoryPage.vue
└── QuestionManagePage.vue
    └── QuestionForm.vue        # 添加/导入题目表单
```

## 9. Celery 任务

| 任务 | 触发 | 输入 | 输出 |
|------|------|------|------|
| parse_resume | 上传后 | 文件路径 | 简历 JSON |
| match_jobs | 解析后 | 技能标签 | 岗位列表 |
| agent_interview_step | 每轮提交答案 | 会话状态 + 回答 | 评分 + 下一题/结束 |
| generate_report | 面试结束 | 完整历史 | 综合报告 |
| embed_questions | 导入题目 | 题目列表 | 向量入库 |

## 10. 目录结构

```
ai-interview/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/
│   │   ├── resume.py
│   │   ├── interview.py
│   │   └── question.py
│   ├── routes/
│   │   ├── resume_api.py
│   │   ├── interview_api.py
│   │   └── question_api.py
│   ├── services/
│   │   ├── deepseek.py          # LLM 调用封装
│   │   ├── dashscope.py         # Embedding
│   │   └── rag.py               # pgvector 语义检索
│   ├── agent/                    # 🆕 Agent 模块
│   │   ├── interviewer.py       # 面试官 Agent 核心逻辑
│   │   ├── tools.py             # Agent 工具集（RAG/出题/评分）
│   │   └── prompts.py           # System prompt 模板
│   ├── tasks/
│   │   ├── celery_app.py
│   │   ├── resume_tasks.py
│   │   ├── interview_tasks.py
│   │   └── question_tasks.py
│   └── schemas/
│       ├── resume.py
│       ├── interview.py
│       └── question.py
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.js / App.vue
│       ├── router/index.js
│       ├── views/  (6 个页面)
│       ├── components/ (6 个组件)
│       └── api/index.js
├── seed_data/
│   └── questions.json
├── alembic/ + alembic.ini
└── docs/superpowers/specs/
```
