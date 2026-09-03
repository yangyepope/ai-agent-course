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
            "k": 5,
            "num_candidates": 50,
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
        top_k: int = 5,
    ):
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
                                    "match": {
                                        "content": query
                                    }
                                }
                            }
                        },
                        {
                            "knn": {
                                "field": "embedding",
                                "query_vector": query_vector,
                                "k": 20,
                                "num_candidates": 100,
                            }
                        }
                    ],
                    "rank_constant": 60,
                    "rank_window_size": 50,
                }
            },
            size=top_k,
        )

        return response["hits"]["hits"]



# 测试代码
from app.elasticsearch_client import ElasticsearchClient

# from app.search_service import SearchService

es = ElasticsearchClient()

service = SearchService(
    es.get_client()
)

results = service.keyword_search(
    "Redis maxmemory-policy",tenant_id="tenant_1", top_k=5
)

for result in results:

    print(
        result["_score"],
        result["_source"]["content"]
    )
