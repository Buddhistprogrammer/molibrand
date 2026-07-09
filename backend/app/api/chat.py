"""对话：SSE 流式诊断对话。核心链路（架构 6.2「用户对话流程」）。"""
import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core import CurrentUser, DBSession, get_current_user
from app.db.session import MySQLSession, PGSession
from app.models import ChatMessage, Consultation, User
from app.schemas import ChatIn, ConsultationOut, MessageOut
from app.services import llm, rag

router = APIRouter(prefix="/api", tags=["chat"])

_SYSTEM_PROMPT = (
    "你是资深品牌咨询专家茉莉总的 AI 分身，服务中小企业老板。"
    "请仅基于检索到的【知识库片段】进行专业品牌诊断，主动追问关键信息"
    "（品牌定位、目标用户、竞品差异等），避免泛泛而谈。"
)


@router.post("/consultations", response_model=ConsultationOut)
async def create_consultation(user: CurrentUser, db: DBSession):
    c = Consultation(user_id=user.id, title="新的品牌诊断", status="active")
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return c


@router.get("/consultations", response_model=list[ConsultationOut])
async def list_consultations(user: CurrentUser, db: DBSession):
    rows = await db.scalars(
        select(Consultation)
        .where(Consultation.user_id == user.id)
        .order_by(Consultation.updated_at.desc())
    )
    return list(rows)


@router.get("/consultations/{cid}/messages", response_model=list[MessageOut])
async def list_messages(cid: int, user: CurrentUser, db: DBSession):
    await _owned_consultation(cid, user, db)
    rows = await db.scalars(
        select(ChatMessage)
        .where(ChatMessage.consultation_id == cid)
        .order_by(ChatMessage.created_at)
    )
    return list(rows)


@router.post("/chat")
async def post_message(body: ChatIn, user: CurrentUser, db: DBSession):
    """保存用户消息，返回可用于 SSE 拉流的 token。前端随后 GET /api/chat/stream。"""
    cid = body.consultation_id
    if cid is None:
        c = Consultation(user_id=user.id, title=body.message[:20] or "新的品牌诊断")
        db.add(c)
        await db.commit()
        await db.refresh(c)
        cid = c.id
    else:
        await _owned_consultation(cid, user, db)

    attachments = [a.model_dump() for a in body.attachments]
    ctype = "mixed" if attachments else "text"
    db.add(
        ChatMessage(
            consultation_id=cid,
            role="user",
            content=body.message,
            content_type=ctype,
            attachments=attachments or None,
        )
    )
    await db.commit()
    return {"consultation_id": cid}


@router.get("/chat/stream")
async def chat_stream(
    consultation_id: int,
    user: Annotated[User, Depends(get_current_user)],
):
    """SSE 流式输出 AI 回复。EventSource 无法带 header，鉴权用 query token 由前端封装。"""

    async def event_generator():
        async with MySQLSession() as db, PGSession() as pg:
            # 1. 权限校验 + 拉取历史
            c = await db.scalar(
                select(Consultation).where(
                    Consultation.id == consultation_id,
                    Consultation.user_id == user.id,
                )
            )
            if c is None:
                yield _sse({"error": "会话不存在"})
                return

            history_rows = await db.scalars(
                select(ChatMessage)
                .where(ChatMessage.consultation_id == consultation_id)
                .order_by(ChatMessage.created_at)
            )
            history = list(history_rows)
            last_user = next((m for m in reversed(history) if m.role == "user"), None)
            query_text = last_user.content if last_user else ""

            # 2. RAG 检索
            chunks = await rag.search(query_text, pg, top_k=5)
            knowledge = "\n---\n".join(c["content"] for c in chunks)

            # 3. 组装 messages（滑动窗口保留最近 10 轮，架构 8.3）
            messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
            if knowledge:
                messages.append(
                    {"role": "system", "content": f"【知识库片段】\n{knowledge}"}
                )
            for m in history[-20:]:
                if m.role in ("user", "assistant"):
                    if m.attachments:
                        content = llm.build_omni_content(m.content, m.attachments)
                        messages.append({"role": m.role, "content": content})
                    else:
                        messages.append({"role": m.role, "content": m.content})

            # 4. 流式输出并累积
            full = ""
            model = settings.llm_omni_model if _has_media(history) else settings.llm_chat_model
            async for delta in llm.chat_stream(messages, model=model):
                full += delta
                yield _sse({"delta": delta})

            # 5. 落库
            db.add(
                ChatMessage(
                    consultation_id=consultation_id,
                    role="assistant",
                    content=full,
                    rag_chunks=[c["id"] for c in chunks] or None,
                )
            )
            await db.commit()
            yield _sse({"done": True, "consultation_id": consultation_id})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _has_media(history: list[ChatMessage]) -> bool:
    return any(m.attachments for m in history)


async def _owned_consultation(cid: int, user: User, db: AsyncSession) -> Consultation:
    c = await db.scalar(
        select(Consultation).where(
            Consultation.id == cid, Consultation.user_id == user.id
        )
    )
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "会话不存在")
    return c
