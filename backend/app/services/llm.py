"""百炼 DashScope 封装：对话（流式）、Embedding、多模态。

未配置 DASHSCOPE_API_KEY 时降级为 mock，方便本地起服务与联调前端。
参考 Architecture.md 3.1 / 8.1。
"""
from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from app.config import settings

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.dashscope_api_key,
            base_url=settings.dashscope_base_url,
        )
    return _client


async def embed(text: str) -> list[float]:
    """文本向量化（text-embedding-v4）。降级时返回零向量。"""
    if not settings.llm_enabled:
        return [0.0] * settings.embedding_dim
    resp = await _get_client().embeddings.create(
        model=settings.embedding_model,
        input=text,
        dimensions=settings.embedding_dim,
    )
    return resp.data[0].embedding


async def chat_stream(
    messages: list[dict],
    model: str | None = None,
) -> AsyncGenerator[str, None]:
    """流式对话，逐段 yield 文本增量。

    messages 为 OpenAI 格式，content 可为字符串或多模态数组（图片/视频 URL）。
    """
    if not settings.llm_enabled:
        async for chunk in _mock_stream(messages):
            yield chunk
        return

    stream = await _get_client().chat.completions.create(
        model=model or settings.llm_chat_model,
        messages=messages,
        stream=True,
    )
    async for event in stream:
        delta = event.choices[0].delta.content if event.choices else None
        if delta:
            yield delta


async def chat_complete(messages: list[dict], model: str | None = None) -> str:
    """非流式一次性补全（用于报告生成等）。"""
    if not settings.llm_enabled:
        return "".join([c async for c in _mock_stream(messages)])
    resp = await _get_client().chat.completions.create(
        model=model or settings.llm_chat_model,
        messages=messages,
    )
    return resp.choices[0].message.content or ""


async def _mock_stream(messages: list[dict]) -> AsyncGenerator[str, None]:
    """降级 mock：无 API Key 时返回占位回复。"""
    last = messages[-1]["content"] if messages else ""
    if isinstance(last, list):  # 多模态
        last = " ".join(p.get("text", "[附件]") for p in last)
    reply = (
        f"【本地 Mock 回复｜未配置 DASHSCOPE_API_KEY】\n"
        f"我已收到你的描述：{last[:60]}...\n"
        f"为了做品牌诊断，请补充：1) 你的目标用户是谁？"
        f"2) 与竞品最大的差异点？3) 当前品牌最困扰你的问题？"
    )
    for word in reply:
        yield word


def build_omni_content(text: str, attachments: list[dict]) -> list[dict]:
    """把文字 + 附件 URL 组装为多模态 content 数组。"""
    content: list[dict] = []
    if text:
        content.append({"type": "text", "text": text})
    for att in attachments:
        t, url = att.get("type"), att.get("url")
        if t == "image":
            content.append({"type": "image_url", "image_url": {"url": url}})
        elif t == "video":
            content.append({"type": "video_url", "video_url": {"url": url}})
        # audio 走 ASR 转文字后并入 text，不在此处
    return content or [{"type": "text", "text": ""}]
