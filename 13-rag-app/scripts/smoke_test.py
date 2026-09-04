"""
冒烟测试：不起 HTTP 服务，直接把检索链路跑一遍。

    python -m scripts.smoke_test          # 只跑召回 + 精排（不花 LLM 的钱）
    python -m scripts.smoke_test --llm    # 连生成一起跑

每条 query 都会打印召回名次和精排名次的对照，
用来看清精排把什么提上来了、把什么压下去了。
"""

import sys

from app.config import ES_INDEX
from app.context import ContextBuilder
from app.elasticsearch_client import ElasticsearchClient
from app.embedding import EmbeddingService
from app.index_manager import IndexManager
from app.llm import LLMService
from app.logging_config import setup_logging
from app.rag_service import RAGService
from app.reranker import SimpleReranker
from app.retriever import Retriever

# (租户, query, 这条想验证什么)
CASES = [
    (
        "tenant-001",
        "maxmemory-policy",
        "专有名词：BM25 该稳稳命中",
    ),
    (
        "tenant-001",
        "Redis内存满了怎么淘汰",
        "换个说法：字面不含 maxmemory-policy，靠向量命中",
    ),
    (
        "tenant-001",
        "缓存里的数据同时失效导致数据库被打挂怎么办",
        "整句自然语言：字面几乎不重叠，看向量能否找到缓存雪崩",
    ),
    (
        "tenant-001",
        "内存不够用了",
        "歧义词：Redis 内存和 Java 堆内存都含「内存」",
    ),
    (
        "tenant-001",
        "日志是怎么记录的",
        "歧义词：AOF、binlog、GC 日志、Kafka 日志压缩都沾「日志」",
    ),
    (
        "tenant-001",
        "为什么加了索引还是慢",
        "跨文档：回表、索引失效、EXPLAIN 都相关",
    ),
    (
        "tenant-002",
        "住宿费能报多少",
        "另一个租户：应只返回 finance 的内容",
    ),
    (
        "tenant-002",
        "Redis 怎么配置淘汰策略",
        "租户隔离：tenant-002 没有技术文档，不该看到 tenant-001 的内容",
    ),
    (
        "tenant-001",
        "怎么申请年假",
        "知识库外：tenant-001 没有 HR 文档，答案应是「没找到」",
    ),
]


def show(title: str, documents: list[dict]) -> None:
    print(f"  {title}")

    if not documents:
        print("    （空）")
        return

    for index, document in enumerate(documents, start=1):
        source = document["_source"]

        rerank_score = document.get("_rerank_score")

        rerank_text = f"{rerank_score:.3f}" if rerank_score is not None else "  -  "

        print(
            f"    #{index} {source['chunk_id']:>9}"
            f"  rrf={document.get('_score', 0.0):.6f}"
            f"  rerank={rerank_text}"
            f"  [{source['category']}] {source['content'][:34]}"
        )


def main() -> None:
    setup_logging()

    with_llm = "--llm" in sys.argv

    es_client = ElasticsearchClient()

    if not es_client.ping():
        raise RuntimeError("连不上 Elasticsearch")

    index_manager = IndexManager(es_client.get_client())

    if not index_manager.exists():
        raise RuntimeError(f"索引 {ES_INDEX} 不存在，先跑 scripts.init_index")

    count = index_manager.count()

    if count == 0:
        raise RuntimeError(f"索引 {ES_INDEX} 是空的，先跑 scripts.index_documents")

    print(f"索引 {ES_INDEX}：{count} 条文档")
    print("加载 Embedding 模型…\n", flush=True)

    retriever = Retriever(
        client=es_client.get_client(),
        embedding_service=EmbeddingService(),
    )

    reranker = SimpleReranker()

    rag_service = RAGService(
        retriever=retriever,
        reranker=reranker,
        context_builder=ContextBuilder(),
        llm=LLMService() if with_llm else None,  # type: ignore[arg-type]
    )

    leaks = 0

    for tenant_id, query, intent in CASES:
        print("=" * 78)
        print(f"[{tenant_id}] {query}")
        print(f"  ▸ {intent}\n")

        retrieved = retriever.search(
            query=query,
            tenant_id=tenant_id,
            top_k=RAGService.CANDIDATE_SIZE,
        )

        show(f"召回 {len(retrieved)} 条（按 RRF 分）：", retrieved[:5])

        print()

        reranked = reranker.rerank(
            query=query,
            documents=retrieved,
            top_k=3,
        )

        show("精排后 top 3（按精排分）：", reranked)

        # 租户隔离校验：任何一条串了租户都算失败
        crossed = [
            document["_source"]["chunk_id"]
            for document in retrieved
            if document["_source"]["tenant_id"] != tenant_id
        ]

        if crossed:
            leaks += 1
            print(f"\n  ✗ 租户泄漏：{crossed}")

        if with_llm:
            result = rag_service.answer(
                query=query,
                tenant_id=tenant_id,
                top_k=3,
            )
            print(f"\n  答案：{result['answer'][:180]}")

        print()

    print("=" * 78)

    if leaks:
        print(f"租户隔离：✗ 有 {leaks} 条 query 串了租户")
        sys.exit(1)

    print(f"租户隔离：✓ {len(CASES)} 条 query 全部只返回本租户数据")


if __name__ == "__main__":
    main()
