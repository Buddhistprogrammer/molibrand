"""诊断报告生成：综合对话历史 + 知识库，产出结构化 JSON（架构 6.2 / PRD P0-4）。"""
import json

from app.services import llm, rag
from sqlalchemy.ext.asyncio import AsyncSession

# 结构化报告骨架（对应 PRD「品牌现状评估 / 问题分析 / 改进建议」）
REPORT_SCHEMA = {
    "brand_summary": "品牌一句话概述",
    "current_assessment": "品牌现状评估",
    "core_problems": ["问题1", "问题2"],
    "positioning_advice": "品牌定位建议",
    "differentiation": "差异化建议",
    "action_plan": ["可落地步骤1", "可落地步骤2"],
    "health_score": {"awareness": 0, "differentiation": 0, "consistency": 0},
}

_SYSTEM_PROMPT = (
    "你是资深品牌咨询专家茉莉总的 AI 分身。请严格基于【知识库片段】和【对话记录】"
    "为用户生成结构化品牌诊断报告。只输出 JSON，不要多余文字。字段如下：\n"
    + json.dumps(REPORT_SCHEMA, ensure_ascii=False, indent=2)
    + "\nhealth_score 各维度 0-100 整数。若信息不足，在对应字段注明需补充的信息。"
)


async def generate_report(history: list[dict], pg: AsyncSession) -> dict:
    """基于对话历史生成诊断报告 JSON。"""
    convo = "\n".join(f"{m['role']}: {m['content']}" for m in history)
    chunks = await rag.search(convo[-1000:], pg, top_k=5)
    knowledge = "\n---\n".join(c["content"] for c in chunks) or "（暂无命中知识库）"

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"【知识库片段】\n{knowledge}\n\n【对话记录】\n{convo}\n\n请生成诊断报告 JSON。",
        },
    ]
    raw = await llm.chat_complete(messages)
    return _parse_json(raw)


def _parse_json(raw: str) -> dict:
    """容错解析模型输出的 JSON。"""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1].removeprefix("json").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # mock 或解析失败时返回带原文的草稿骨架
        draft = dict(REPORT_SCHEMA)
        draft["brand_summary"] = "（AI 草稿待人工完善）"
        draft["current_assessment"] = raw[:500] or "信息不足，请继续对话补充品牌信息。"
        return draft
