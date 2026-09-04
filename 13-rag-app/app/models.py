from typing import Any

from pydantic import BaseModel, Field


class Source(BaseModel):
    """
    RAG 最终返回的知识来源。
    """

    chunk_id: str

    source: str

    page: int

    score: float = Field(
        description="ES 的 RRF 融合分",
    )

    rerank_score: float | None = Field(
        default=None,
        description="Reranker 打的分（0~1 覆盖率）",
    )


class RAGRequest(BaseModel):
    """
    用户发送给 RAG API 的请求。
    """

    query: str = Field(
        min_length=1,
        description="用户问题",
    )

    tenant_id: str = Field(
        min_length=1,
        description="租户 ID",
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="最终返回多少个 Chunk",
    )

    debug: bool = Field(
        default=False,
        description=(
            "返回各阶段中间产物（召回名次、"
            "精排名次、Context、Prompt）。"
            "会把知识库原文和 Prompt 一起吐出来，"
            "生产环境别开。"
        ),
    )


class RankedChunk(BaseModel):
    """
    debug 用：某个阶段结束后，一条 Chunk 的名次和得分。
    """

    rank: int

    chunk_id: str

    score: float = Field(
        description="ES 的 RRF 融合分",
    )

    rerank_score: float | None = Field(
        default=None,
        description="精排分，召回阶段还没有",
    )


class RAGDebug(BaseModel):
    """
    一次问答的中间产物，用来看清每一步做了什么。
    """

    retrieval_size: int = Field(
        description="Retriever 实际召回几条",
    )

    retrieved: list[RankedChunk] = Field(
        description="召回结果，按 RRF 分排序",
    )

    reranked: list[RankedChunk] = Field(
        description="精排后的结果，按精排分排序",
    )

    context_chars: int = Field(
        description="拼出来的 Context 有多少字",
    )

    context: str = Field(
        description="喂给 LLM 的 Context 原文",
    )

    messages: list[dict[str, Any]] = Field(
        description="实际发给 LLM 的 messages",
    )


class RAGResponse(BaseModel):
    """
    RAG API 返回结果。
    """

    answer: str

    sources: list[Source]

    request_id: str | None = Field(
        default=None,
        description="本次请求的追踪 id，可用它到日志里定位",
    )

    debug: RAGDebug | None = Field(
        default=None,
        description="仅当请求里 debug=true 时返回",
    )
