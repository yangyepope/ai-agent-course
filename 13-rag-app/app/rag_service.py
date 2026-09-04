import time
from typing import Any

from app.context import ContextBuilder
from app.llm import LLMService
from app.logging_config import get_logger
from app.prompt import build_messages
from app.reranker import SimpleReranker
from app.retriever import Retriever
from openai.types.chat import ChatCompletionMessageParam

logger = get_logger(__name__)


def to_ranked(documents: list[dict]) -> list[dict]:
    """
    把某个阶段的 hits 压成「名次 + 两个分数」。

    只列 chunk_id 是不够的：光看 id 换了顺序，
    看不出精排凭什么这么排。带上 score（ES 的 RRF 分）
    和 rerank_score（精排分）才能对账。
    """

    return [
        {
            "rank": index + 1,
            "chunk_id": document["_source"]["chunk_id"],
            "score": document.get("_score", 0.0),
            "rerank_score": document.get("_rerank_score"),
        }
        for index, document in enumerate(documents)
    ]


def build_debug(
    retrieved_documents: list[dict],
    reranked_documents: list[dict],
    context: str,
    messages: list[ChatCompletionMessageParam],
) -> dict[str, Any]:
    """
    汇总一次问答的中间产物。

    对着看 retrieved 和 reranked 两份名次，
    就能知道精排到底改变了什么。
    """

    return {
        "retrieval_size": len(retrieved_documents),
        "retrieved": to_ranked(retrieved_documents),
        "reranked": to_ranked(reranked_documents),
        "context_chars": len(context),
        "context": context,
        "messages": [dict(message) for message in messages],
    }


class RAGService:
    # 召回多少条送进精排。比 top_k 大，精排才有东西可挑
    CANDIDATE_SIZE = 10

    def __init__(
        self,
        retriever: Retriever,
        reranker: SimpleReranker,
        context_builder: ContextBuilder,
        llm: LLMService,
    ):
        self.retriever = retriever
        self.reranker = reranker
        self.context_builder = context_builder
        self.llm = llm

    def answer(
        self,
        query: str,
        tenant_id: str,
        top_k: int = 5,
        debug: bool = False,
    ):

        started = time.perf_counter()

        logger.info(
            "RAG 开始 | tenant=%s top_k=%d debug=%s | query=%r",
            tenant_id,
            top_k,
            debug,
            query,
        )

        # 1. Retrieval
        retrieve_started = time.perf_counter()

        retrieved_documents = self.retriever.search(
            query=query,
            tenant_id=tenant_id,
            top_k=self.CANDIDATE_SIZE,
        )

        retrieve_ms = (time.perf_counter() - retrieve_started) * 1000

        # 2. Reranking
        rerank_started = time.perf_counter()

        reranked_documents = self.reranker.rerank(
            query=query,
            documents=retrieved_documents,
            top_k=top_k,
        )

        rerank_ms = (time.perf_counter() - rerank_started) * 1000

        # 3. Build Context
        context, sources = self.context_builder.build(reranked_documents)

        # 4. Build Prompt
        messages = build_messages(
            query=query,
            context=context,
        )

        # 5. Generate Answer
        llm_started = time.perf_counter()

        answer = self.llm.chat(messages)

        llm_ms = (time.perf_counter() - llm_started) * 1000

        total_ms = (time.perf_counter() - started) * 1000

        # 一次问答的耗时账：四个阶段量级差很多，
        # 出问题时先看这一行就知道该往哪查
        logger.info(
            "RAG 完成 | 总计 %.0fms = 召回 %.0f + 精排 %.0f "
            "+ 生成 %.0f | 引用 %d 个 Chunk | 答案 %d 字",
            total_ms,
            retrieve_ms,
            rerank_ms,
            llm_ms,
            len(sources),
            len(answer),
        )

        result: dict[str, Any] = {
            "answer": answer,
            "sources": sources,
        }

        # debug 会把知识库原文和 Prompt 一起吐出来，
        # 所以做成开关，默认关掉
        if debug:
            result["debug"] = build_debug(
                retrieved_documents=retrieved_documents,
                reranked_documents=reranked_documents,
                context=context,
                messages=messages,
            )

        return result


# 你现在可以将answer() 理解为：
"""
                    answer()
                       │
                       ▼
                  Retriever
                       │
                       ▼
                召回 10 个 Chunk
                       │
                       ▼
                  Reranker
                       │
                       ▼
                 保留 5 个 Chunk
                       │
                       ▼
               Context Builder
                       │
                       ▼
                    Context
                       │
                       ▼
                     Prompt
                       │
                       ▼
                      LLM
                       │
                       ▼
                    Answer
"""
