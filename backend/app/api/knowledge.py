"""知识库管理：录入文档、触发向量化、列表（reviewer/admin，PRD P0-1）。"""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import DBSession, ReviewerUser
from app.db.session import get_pg
from app.models import KnowledgeDocument
from app.schemas import KnowledgeDocIn, KnowledgeDocOut
from app.services import rag

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("/documents", response_model=list[KnowledgeDocOut])
async def list_docs(_: ReviewerUser, db: DBSession):
    return await rag.list_documents(db)


@router.post("/documents", response_model=KnowledgeDocOut)
async def create_doc(
    body: KnowledgeDocIn,
    _: ReviewerUser,
    db: DBSession,
    pg: Annotated[AsyncSession, Depends(get_pg)],
):
    doc = KnowledgeDocument(
        title=body.title,
        content=body.content,
        doc_type=body.doc_type,
        tags=body.tags,
        source_url=body.source_url,
        status="pending",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # 同步分块 + 向量化（生产可改为后台任务队列）
    await rag.index_document(doc, db, pg)
    await db.refresh(doc)
    return doc
