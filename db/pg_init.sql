-- ============================================================
-- PostgreSQL + pgvector 向量存储初始化
-- 参考 Architecture.md 7.4 / 10.4
-- ============================================================

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS knowledge_embeddings (
    id          BIGSERIAL PRIMARY KEY,
    doc_id      BIGINT NOT NULL,               -- 对应 MySQL knowledge_documents.id
    chunk_index INT    NOT NULL,
    content     TEXT   NOT NULL,
    embedding   vector(1024),                  -- text-embedding-v4 默认 1024 维
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- HNSW 索引（余弦相似度，高性能近似最近邻）
CREATE INDEX IF NOT EXISTS idx_knowledge_embeddings_vector
    ON knowledge_embeddings USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_knowledge_embeddings_doc
    ON knowledge_embeddings (doc_id);
