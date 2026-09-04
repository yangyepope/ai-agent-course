import time

from app.config import ES_INDEX
from app.embedding import EmbeddingService
from app.logging_config import get_logger
from elasticsearch import Elasticsearch

logger = get_logger(__name__)


class Retriever:
    def __init__(
        self,
        client: Elasticsearch,
        embedding_service: EmbeddingService,
    ):
        self.client = client
        self.embedding_service = embedding_service

    def search(
        self,
        query: str,
        tenant_id: str,
        top_k: int = 10,
    ) -> list[dict]:

        # 1. 将 Query 转成向量
        embed_started = time.perf_counter()

        query_vector = self.embedding_service.embed(query)

        embed_ms = (time.perf_counter() - embed_started) * 1000

        # 2. Elasticsearch Hybrid Search
        search_started = time.perf_counter()

        response = self.client.search(
            index=ES_INDEX,
            retriever={
                "rrf": {
                    "retrievers": [
                        # -------------------------
                        # BM25
                        # -------------------------
                        {
                            "standard": {
                                "query": {
                                    "bool": {
                                        "must": [{"match": {"content": query}}],
                                        "filter": [{"term": {"tenant_id": tenant_id}}],
                                    }
                                }
                            }
                        },
                        # -------------------------
                        # Vector Search
                        # -------------------------
                        {
                            "knn": {
                                "field": "embedding",
                                "query_vector": query_vector,
                                "k": 50,
                                "num_candidates": 100,
                                "filter": {"term": {"tenant_id": tenant_id}},
                            }
                        },
                    ],
                    # RRF 参数
                    "rank_constant": 60,
                    "rank_window_size": 50,
                }
            },
            # 最终召回数量
            size=top_k,
        )

        search_ms = (time.perf_counter() - search_started) * 1000

        hits = response["hits"]["hits"]

        logger.info(
            "召回 %d 条 | embed %.0fms | es %.0fms | index=%s tenant=%s top_k=%d",
            len(hits),
            embed_ms,
            search_ms,
            ES_INDEX,
            tenant_id,
            top_k,
        )

        if not hits:
            logger.warning(
                "召回为空：tenant=%s query=%r",
                tenant_id,
                query,
            )

        return hits
