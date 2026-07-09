"""诊断报告 + 人工审核工作台（PRD P0-4/5/6）。

用户：生成报告、查看已下发报告。
审核员：查看待审报告、通过/驳回/修改后下发。
"""
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import CurrentUser, DBSession, ReviewerUser
from app.db.session import get_pg
from app.models import ChatMessage, Consultation, DiagnosticReport
from app.schemas import ReportOut, ReviewAction
from app.services import report as report_svc

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/generate/{consultation_id}", response_model=ReportOut)
async def generate(
    consultation_id: int,
    user: CurrentUser,
    db: DBSession,
    pg: Annotated[AsyncSession, Depends(get_pg)],
):
    """基于会话生成诊断报告草稿，进入待审核状态。"""
    c = await db.scalar(
        select(Consultation).where(
            Consultation.id == consultation_id, Consultation.user_id == user.id
        )
    )
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "会话不存在")

    rows = await db.scalars(
        select(ChatMessage)
        .where(ChatMessage.consultation_id == consultation_id)
        .order_by(ChatMessage.created_at)
    )
    history = [{"role": m.role, "content": m.content} for m in rows]
    content = await report_svc.generate_report(history, pg)

    rpt = DiagnosticReport(
        consultation_id=consultation_id,
        user_id=user.id,
        content=content,
        status="pending_review",
    )
    c.status = "reviewing"
    db.add(rpt)
    await db.commit()
    await db.refresh(rpt)
    return rpt


@router.get("/mine", response_model=list[ReportOut])
async def my_reports(user: CurrentUser, db: DBSession):
    """用户查看自己的报告（仅展示已下发/审核中状态）。"""
    rows = await db.scalars(
        select(DiagnosticReport)
        .where(DiagnosticReport.user_id == user.id)
        .order_by(DiagnosticReport.created_at.desc())
    )
    return list(rows)


# ---------- 审核工作台 ----------
@router.get("/pending", response_model=list[ReportOut])
async def pending_reports(_: ReviewerUser, db: DBSession):
    rows = await db.scalars(
        select(DiagnosticReport)
        .where(DiagnosticReport.status == "pending_review")
        .order_by(DiagnosticReport.created_at)
    )
    return list(rows)


@router.post("/{report_id}/review", response_model=ReportOut)
async def review(report_id: int, body: ReviewAction, reviewer: ReviewerUser, db: DBSession):
    rpt = await db.scalar(
        select(DiagnosticReport).where(DiagnosticReport.id == report_id)
    )
    if rpt is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "报告不存在")

    rpt.reviewer_id = reviewer.id
    rpt.review_comment = body.comment
    rpt.reviewed_at = datetime.now(timezone.utc)

    if body.action == "revise" and body.content is not None:
        rpt.content = body.content

    if body.action == "reject":
        rpt.status = "rejected"
    else:  # approve / revise → 通过并下发
        rpt.status = "delivered"
        rpt.delivered_at = datetime.now(timezone.utc)
        c = await db.scalar(
            select(Consultation).where(Consultation.id == rpt.consultation_id)
        )
        if c:
            c.status = "completed"

    await db.commit()
    await db.refresh(rpt)
    return rpt
