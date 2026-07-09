"""SQLAlchemy ORM 模型（MySQL 业务表），与 db/mysql_init.sql 对应。"""
from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    phone: Mapped[str] = mapped_column(String(32), unique=True)
    nickname: Mapped[str | None] = mapped_column(String(64))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(Enum("user", "reviewer", "admin"), default="user")
    plan: Mapped[str] = mapped_column(
        Enum("none", "single", "monthly", "annual"), default="none"
    )
    quota_left: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    doc_type: Mapped[str] = mapped_column(
        Enum("methodology", "case", "template", "faq")
    )
    tags: Mapped[dict | None] = mapped_column(JSON)
    source_url: Mapped[str | None] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(
        Enum("pending", "chunked", "indexed", "error"), default="pending"
    )
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    doc_id: Mapped[int] = mapped_column(ForeignKey("knowledge_documents.id"))
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int | None] = mapped_column(Integer)
    pgvector_id: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Consultation(Base):
    __tablename__ = "consultations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(
        Enum("active", "reporting", "reviewing", "completed", "closed"),
        default="active",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    consultation_id: Mapped[int] = mapped_column(ForeignKey("consultations.id"))
    role: Mapped[str] = mapped_column(Enum("user", "assistant", "system"))
    content: Mapped[str] = mapped_column(Text)
    content_type: Mapped[str] = mapped_column(
        Enum("text", "image", "audio", "video", "mixed"), default="text"
    )
    attachments: Mapped[list | None] = mapped_column(JSON)
    token_count: Mapped[int | None] = mapped_column(Integer)
    rag_chunks: Mapped[list | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class DiagnosticReport(Base):
    __tablename__ = "diagnostic_reports"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    consultation_id: Mapped[int] = mapped_column(ForeignKey("consultations.id"))
    user_id: Mapped[int] = mapped_column(BigInteger)
    content: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(
        Enum("draft", "pending_review", "approved", "rejected", "delivered"),
        default="draft",
    )
    reviewer_id: Mapped[int | None] = mapped_column(BigInteger)
    review_comment: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger)
    action: Mapped[str] = mapped_column(String(64))
    target: Mapped[str | None] = mapped_column(String(128))
    detail: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
