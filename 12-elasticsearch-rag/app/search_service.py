from app.index_manager import INDEX_NAME
from elasticsearch import Elasticsearch


class SearchService:

    def __init__(
        self,
        client: Elasticsearch,
    ):
        self.client = client

    # def keyword_search(
    #     self,
    #     query: str,
    #     top_k: int = 5,
    # ):

    #     response = self.client.search(
    #         index=INDEX_NAME,
    #         query={
    #             "match": {
    #                 "content": query
    #             }
    #         },
    #         size=top_k,
    #     )

    #     return response["hits"]["hits"]

    # 优化为ES Filter
    def keyword_search(
        self,
        query: str,
        tenant_id: str,
        top_k: int = 5,
    ):

        response = self.client.search(
            index=INDEX_NAME,
            query={
                "bool": {
                    "must": [
                        {
                            "match": {
                                "content": query
                            }
                        }
                    ],
                    "filter": [
                        {
                            "term": {
                                "tenant_id": tenant_id
                            }
                        }
                    ]
                }
            },
            size=top_k,
        )

        return response["hits"]["hits"]


    # 添加Vector Search
    def vector_search(
        self,
        query: str,
        embedding_service,
        tenant_id: str,
        top_k: int = 5,
        num_candidates: int = 50,
    ):
        query_vector = (
            embedding_service.embed(query)
        )

        response = self.client.search(
            index=INDEX_NAME,
            # knn={
            #     "field": "embedding",
            #     "query_vector": query_vector,

            #     #                 为什么有两个参数？

            #     # 这是 RAG 开发中非常容易被问到的问题：

            #     # k
            #     # num_candidates

            #     # 例如：

            #     # knn={
            #     #     "field": "embedding",
            #     #     "query_vector": query_vector,
            #     #     "k": 5,
            #     #     "num_candidates": 50,
            #     # }

            #     # 意思大概是：

            #     # 先找候选：

            #     # 50

            #     # 然后最终：

            #     # 5

            #     # 所以：

            #     # num_candidates
            #     #         ↓
            #     #    Candidate Pool
            #     #         ↓
            #     #         5
            #     #         ↓
            #     #        Top K

            #     # 通常：

            #     # num_candidates > k
            #     "k": top_k,
            #     "num_candidates": num_candidates,
            # },

            # Vector Search 也可以 Filter
            knn={
                "field": "embedding",
                "query_vector": query_vector,
                "k": top_k,
                "num_candidates": num_candidates,
                "filter": {
                    "term": {
                        "tenant_id": tenant_id
                    }
                }
            },
            size=top_k,
        )

        return response["hits"]["hits"]


    def hybrid_search(
        self,
        query: str,
        embedding_service,
        tenant_id: str,
        top_k: int = 5,
        candidate_k: int | None = None,
    ):
        # candidate_k 是给精排（reranker.py）留的候选池。
        # 精排的前提是候选够多：5 条里精排 5 条等于没排。
        # 不传 candidate_k 时行为跟以前完全一样。
        size = (
            candidate_k
            if candidate_k
            else top_k
        )

        # 候选池放大后，knn 和 RRF 的窗口也得跟着放大，
        # 否则 ES 只凑得出 20 条，size=50 也拿不到 50 条
        knn_k = max(20, size)

        rank_window_size = max(50, size)

        num_candidates = max(100, size * 2)

        query_vector = (
            embedding_service.embed(query)
        )

        response = self.client.search(
            index=INDEX_NAME,
            retriever={
                "rrf": {
                    "retrievers": [
                        {
                            "standard": {
                                "query": {
                                    "bool": {
                                        "must": [
                                            {
                                                "match": {
                                                    "content": query
                                                }
                                            }
                                        ],
                                        "filter": [
                                            {
                                                "term": {
                                                    "tenant_id": tenant_id
                                                }
                                            }
                                        ]
                                    }
                                }
                            }
                        },
                        {
                            "knn": {
                                "field": "embedding",
                                "query_vector": query_vector,
                                "k": knn_k,
                                "num_candidates": num_candidates,
                                "filter": {
                                    "term": {
                                        "tenant_id": tenant_id
                                    }
                                }
                            }
                        }
                    ],
                    "rank_constant": 60,
                    "rank_window_size": rank_window_size,
                }
            },
            size=size,
        )

        return response["hits"]["hits"]



# 测试代码（直接运行时执行；被 import 不会触发）
if __name__ == "__main__":

    from app.elasticsearch_client import ElasticsearchClient

    es = ElasticsearchClient()

    service = SearchService(
        es.get_client()
    )

    results = service.keyword_search(
        "Redis maxmemory-policy", tenant_id="tenant-001", top_k=5
    )

    for result in results:

        print(
            result["_score"],
            result["_source"]["content"]
        )
