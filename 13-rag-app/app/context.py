"""
该类的作用如下：
例如 Elasticsearch 返回：

{
  "chunk_id": "redis-001",
  "source": "redis-guide.pdf",
  "page": 15,
  "content": "Redis 的 maxmemory-policy ..."
}

我们转换成：

[来源：redis-guide.pdf 第 15 页]
Redis 的 maxmemory-policy ...

然后多个 Chunk：

Chunk 1
   ↓
Chunk 2
   ↓
Chunk 3

变成：

Context


"""

from app.logging_config import get_logger

logger = get_logger(__name__)


class ContextBuilder:
    def build(
        self,
        documents: list[dict],
    ) -> tuple[str, list[dict]]:

        contexts = []

        sources = []

        for document in documents:
            source = document["_source"]

            context_item = f"[来源：{source['source']} 第 {source['page']} 页]\n{source['content']}"

            contexts.append(context_item)

            sources.append(
                {
                    "chunk_id": source["chunk_id"],
                    "source": source["source"],
                    "page": source["page"],
                    # _score 是 ES 的 RRF 融合分
                    "score": document.get(
                        "_score",
                        0.0,
                    ),
                    # _rerank_score 是 Reranker 打的分，
                    # 没走精排时为 None
                    "rerank_score": document.get("_rerank_score"),
                }
            )

        context = "\n\n".join(contexts)

        logger.info(
            "Context 拼装完成 | %d 个 Chunk | %d 字",
            len(sources),
            len(context),
        )

        # Context 原文只在 DEBUG 打
        logger.debug("Context 内容：\n%s", context)

        return context, sources
