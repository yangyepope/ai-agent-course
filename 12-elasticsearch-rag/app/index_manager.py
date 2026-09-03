from elasticsearch import Elasticsearch

INDEX_NAME = "rag_chunks"


class IndexManager:

    def __init__(self, client: Elasticsearch):
        self.client = client

    def create_index(self):

        if self.client.indices.exists(
            index=INDEX_NAME
        ):
            return

        mappings = {
            "properties": {
                "chunk_id": {
                    "type": "keyword"
                },

                "content": {
                    "type": "text"
                },

                "source": {
                    "type": "keyword"
                },

                "page": {
                    "type": "integer"
                },

                "category": {
                    "type": "keyword"
                },

                "tenant_id": {
                    "type": "keyword"
                },

                "embedding": {
                    "type": "dense_vector",
                    "dims": 512,
                    "index": True,
                    "similarity": "cosine"
                }
            }
        }

        self.client.indices.create(
            index=INDEX_NAME,
            mappings=mappings,
        )


# 这里一定要理解

"""


"content": {
    "type": "text"
}

负责：

BM25

而：

"embedding": {
    "type": "dense_vector",
    "dims": 512,
    "index": true,
    "similarity": "cosine"
}

负责：

Vector Search


也就是说：

              Elasticsearch Document
                       │
          ┌────────────┴────────────┐
          ↓                         ↓
       content                   embedding
          │                         │
          ↓                         ↓
         BM25                      kNN

dense_vector 就是 Elasticsearch 用来存储密集向量并进行 kNN 搜索的核心字段类型

"""
