# 茉莉派 · AI品牌咨询服务产品

基于资深品牌专家（茉莉总）经验知识库 + 阿里云通义全模态大模型，为中小企业老板提供
「AI 诊断 + 人工审核」的品牌咨询方案生成服务。

> 产品需求见 [PRD.md](PRD.md)，技术选型见 [Architecture.md](Architecture.md)，设计规范见 [UIUX.md](UIUX.md)。
> 本仓库为按上述文档落地的**可运行代码骨架（MVP scaffold）**。

---

## 技术栈

| 层 | 选型 |
|----|------|
| 后端 | Python 3.12 + FastAPI（异步）+ SSE 流式 |
| 前端 | React 18 + TypeScript + Vite |
| 大模型 | 阿里云百炼 DashScope（`qwen3.7-plus` / `qwen3.5-omni-plus` / `text-embedding-v4` …）|
| 向量库 | PostgreSQL 16 + pgvector（HNSW 索引）|
| 业务库 | MySQL 8.0 |
| 文件存储 | 阿里云 OSS + STS 前端直传 |
| 部署 | Docker Compose 单机 + Nginx |

> 未配置 `DASHSCOPE_API_KEY` 时，后端自动降级为 **本地 mock 模式**，无需真实 API Key 即可跑通端到端流程。

---

## 目录结构

```
molibrand/
├─ docker-compose.yml        # 一键编排：nginx + app + postgres + mysql + redis
├─ .env.example              # 环境变量模板（复制为 .env）
├─ nginx/nginx.conf          # 反向代理 + SSE 禁缓冲配置
├─ db/
│  ├─ mysql_init.sql         # 业务表（用户/会话/消息/报告/知识库元数据）
│  └─ pg_init.sql            # pgvector 向量表 + HNSW 索引
├─ backend/                  # FastAPI 后端
│  ├─ app/
│  │  ├─ main.py             # 应用入口 + 路由注册 + /api/health
│  │  ├─ config.py           # 环境配置（pydantic-settings）
│  │  ├─ core.py             # JWT / 密码哈希 / 鉴权依赖
│  │  ├─ models.py           # SQLAlchemy ORM（对应 mysql_init.sql）
│  │  ├─ schemas.py          # Pydantic 请求/响应模型
│  │  ├─ db/session.py       # MySQL + PG 异步引擎
│  │  ├─ services/           # llm(百炼) / rag(检索) / oss(STS) / report(报告)
│  │  └─ api/                # auth / chat(SSE) / upload / knowledge / reports
│  ├─ requirements.txt
│  └─ Dockerfile
└─ frontend/                 # React 前端
   └─ src/
      ├─ api.ts              # API 客户端 + fetch 流式 SSE
      ├─ pages/              # Login / Chat / Reports / ReviewConsole / Knowledge
      └─ components/Nav.tsx
```

---

## 核心流程（对应 PRD 第七章）

```
登录 → 发起品牌诊断对话 → AI(RAG 检索知识库) 主动追问 → 用户多模态回答
    → 生成结构化诊断报告(草稿) → 人工审核工作台(通过/驳回/修改) → 下发 → 用户查看
```

对应实现：
- 对话 SSE 流式：[backend/app/api/chat.py](backend/app/api/chat.py) + [frontend/src/pages/Chat.tsx](frontend/src/pages/Chat.tsx)
- RAG 分块/向量化/检索：[backend/app/services/rag.py](backend/app/services/rag.py)
- 报告生成：[backend/app/services/report.py](backend/app/services/report.py) + [backend/app/api/reports.py](backend/app/api/reports.py)
- 人工审核：[frontend/src/pages/ReviewConsole.tsx](frontend/src/pages/ReviewConsole.tsx)

---

## 快速开始

### 方式一：Docker Compose（推荐）

```bash
cp .env.example .env          # 按需填写 DASHSCOPE_API_KEY / OSS（可留空走 mock）
# 构建前端静态资源（nginx 挂载 frontend/dist）
cd frontend && npm install && npm run build && cd ..
docker compose up -d --build
```

- 前端：http://localhost
- 后端 API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/api/health

### 方式二：本地开发

```bash
# 后端
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload    # 需本地/容器 MySQL + PG，见 docker-compose

# 前端（另开终端）
cd frontend
npm install && npm run dev       # http://localhost:5173，/api 已代理到 :8000
```

### 默认账号（本地开发）

`mysql_init.sql` 内置管理员：手机号 `13800000000` / 密码 `admin123`（**上线前务必修改**）。
普通用户可在登录页自助注册，注册赠送 1 次免费诊断。

---

## 主要 API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` `/api/auth/login` | 注册 / 登录，返回 JWT |
| POST | `/api/chat` | 保存用户消息，返回 consultation_id |
| GET  | `/api/chat/stream?consultation_id=` | SSE 流式 AI 回复 |
| GET  | `/api/consultations` `/api/consultations/{id}/messages` | 会话与历史 |
| POST | `/api/upload/sts` | 签发 OSS 上传临时凭证 |
| POST | `/api/reports/generate/{cid}` | 生成诊断报告（进入待审核） |
| GET  | `/api/reports/mine` | 用户查看自己的报告 |
| GET  | `/api/reports/pending` | 审核员：待审核列表 |
| POST | `/api/reports/{id}/review` | 审核员：通过/驳回/修改下发 |
| GET/POST | `/api/knowledge/documents` | 知识库文档列表 / 录入并向量化 |

---

## 待完善（生产化 TODO）

- [ ] 报告/知识库向量化改为后台任务队列（当前同步执行）
- [ ] 接入 `qwen3-rerank` 重排序（当前仅向量 Top-K，见 rag.py 注释）
- [ ] 语音输入 ASR（`fun-asr-realtime`）与 TTS（`cosyvoice`）链路
- [ ] Alembic 数据库迁移（当前用 init.sql）
- [ ] API 调用配额/限流（成本护栏，见 Architecture 9.2）
- [ ] 内容安全审核（多模态上传）
```
