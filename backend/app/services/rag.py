"""RAG 服务：文档分块、向量化入库、向量检索。

参考 Architecture.md 第7章。分块用递归字符切分（512 tokens / 64 overlap）。
向量存 PostgreSQL + pgvector，chunk 元数据存 MySQL。
"""
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import KnowledgeChunk, KnowledgeDocument
from app.services import llm

# 递归分块分隔符优先级（架构 7.1.1）
_SEPARATORS = ["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
_CHUNK_SIZE = 512
_OVERLAP = 64


def split_text(content: str, chunk_size: int = _CHUNK_SIZE, overlap: int = _OVERLAP) -> list[str]:
    """轻量递归字符分块。中文按字符近似 token（架构 7.1.1 说明）。

    生产可替换为 langchain RecursiveCharacterTextSplitter；此处零依赖实现。
    """
    def _recurse(s: str, seps: list[str]) -> list[str]:
        if len(s) <= chunk_size or not seps:
            return [s] if s else []
        sep, rest = seps[0], seps[1:]
        parts = s.split(sep) if sep else list(s)
        chunks, buf = [], ""
        for p in parts:
            piece = p + sep if sep else p
            if len(buf) + len(piece) <= chunk_size:
                buf += piece
            else:
                if buf:
                    chunks.append(buf)
                chunks.extend(_recurse(piece, rest) if len(piece) > chunk_size else [piece])
                buf = ""
        if buf:
            chunks.append(buf)
        return chunks

    raw = [c.strip() for c in _recurse(content, _SEPARATORS) if c.strip()]
    # 加 overlap
    if overlap <= 0 or len(raw) <= 1:
        return raw
    out = [raw[0]]
    for i in range(1, len(raw)):
        tail = raw[i - 1][-overlap:]
        out.append(tail + raw[i])
    return out


async def index_document(doc: KnowledgeDocument, db: AsyncSession, pg: AsyncSession) -> int:
    """对文档分块、向量化并写入 pgvector + MySQL chunk 表。返回 chunk 数。"""
    chunks = split_text(doc.content)
    count = 0
    for idx, chunk in enumerate(chunks):
        vec = await llm.embed(chunk)
        # 写入 pgvector，取回自增 id
        row = await pg.execute(
            text(
                "INSERT INTO knowledge_embeddings (doc_id, chunk_index, content, embedding) "
                "VALUES (:doc_id, :idx, :content, :emb) RETURNING id"
            ),
            {"doc_id": doc.id, "idx": idx, "content": chunk, "emb": str(vec)},
        )
        pgvector_id = row.scalar_one()
        db.add(
            KnowledgeChunk(
                doc_id=doc.id,
                chunk_index=idx,
                content=chunk,
                token_count=len(chunk),
                pgvector_id=pgvector_id,
            )
        )
        count += 1
    await pg.commit()
    doc.chunk_count = count
    doc.status = "indexed"
    await db.commit()
    return count


async def search(query: str, pg: AsyncSession, top_k: int = 5) -> list[dict]:
    """向量检索 Top-K（余弦相似度）。

    生产建议在 Top-10 后接 qwen3-rerank 重排（架构 7.3）；此处返回向量 Top-K。
    """
    if not settings.llm_enabled:
        return []
    vec = await llm.embed(query)
    rows = await pg.execute(
        text(
            "SELECT id, doc_id, chunk_index, content, "
            "1 - (embedding <=> :emb) AS score "
            "FROM knowledge_embeddings "
            "ORDER BY embedding <=> :emb LIMIT :k"
        ),
        {"emb": str(vec), "k": top_k},
    )
    return [dict(r._mapping) for r in rows]


async def list_documents(db: AsyncSession) -> list[KnowledgeDocument]:
    result = await db.scalars(
        select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc())
    )
    return list(result)
