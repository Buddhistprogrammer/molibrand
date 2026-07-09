"""FastAPI 应用入口。"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, chat, knowledge, reports, upload
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("brand-consult")

app = FastAPI(
    title="AI品牌咨询服务 API",
    description="基于茉莉总经验知识库 + 通义全模态大模型的品牌诊断服务",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(upload.router)
app.include_router(knowledge.router)
app.include_router(reports.router)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "env": settings.app_env,
        "llm_enabled": settings.llm_enabled,
        "chat_model": settings.llm_chat_model,
    }


@app.on_event("startup")
async def on_startup():
    if not settings.llm_enabled:
        logger.warning("DASHSCOPE_API_KEY 未配置：LLM/Embedding 走本地 mock 模式。")
