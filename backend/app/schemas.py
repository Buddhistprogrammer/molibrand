"""Pydantic 请求/响应模型。"""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# ---------- 认证 ----------
class RegisterIn(BaseModel):
    phone: str = Field(min_length=6, max_length=32)
    password: str = Field(min_length=6, max_length=64)
    nickname: str | None = None


class LoginIn(BaseModel):
    phone: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    nickname: str | None = None


# ---------- 知识库 ----------
class KnowledgeDocIn(BaseModel):
    title: str
    content: str
    doc_type: Literal["methodology", "case", "template", "faq"]
    tags: list[str] | None = None
    source_url: str | None = None


class KnowledgeDocOut(BaseModel):
    id: int
    title: str
    doc_type: str
    status: str
    chunk_count: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- 附件 ----------
class Attachment(BaseModel):
    type: Literal["image", "audio", "video"]
    url: str


# ---------- 对话 ----------
class ChatIn(BaseModel):
    consultation_id: int | None = None
    message: str = ""
    attachments: list[Attachment] = []


class ConsultationOut(BaseModel):
    id: int
    title: str | None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    content_type: str
    attachments: list[Any] | None
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- 上传 ----------
class STSRequest(BaseModel):
    file_type: Literal["image", "audio", "video", "document"]
    filename: str


class STSResponse(BaseModel):
    access_key_id: str
    access_key_secret: str
    security_token: str
    endpoint: str
    bucket: str
    object_key: str
    expiration: str


# ---------- 报告 ----------
class ReportOut(BaseModel):
    id: int
    consultation_id: int
    content: dict
    status: str
    review_comment: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewAction(BaseModel):
    action: Literal["approve", "reject", "revise"]
    comment: str | None = None
    # revise 时可直接提交修改后的报告内容
    content: dict | None = None
