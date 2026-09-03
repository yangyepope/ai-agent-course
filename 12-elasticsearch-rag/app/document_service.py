import json

from app.embedding import EmbeddingService
from app.index_manager import INDEX_NAME
from elasticsearch import Elasticsearch


class DocumentService:

    def __init__(
        self,
        client: Elasticsearch,
        embedding_service: EmbeddingService,
    ):
        self.client = client
        self.embedding_service = embedding_service

    def load_documents(
        self,
        file_path: str,
    ) -> list[dict]:

        with open(
            file_path,
            "r",
            encoding="utf-8",
        ) as f:
            return json.load(f)

    def index_documents(
        self,
        documents: list[dict],
    ):

        texts = [
            document["content"]
            for document in documents
        ]

        embeddings = (
            self.embedding_service.embed_batch(
                texts
            )
        )

        for document, embedding in zip(
            documents,
            embeddings,
        ):

            body = {
                "chunk_id": document["id"],
                "content": document["content"],
                "source": document["source"],
                "page": document["page"],
                "category": document["category"],
                "tenant_id": document["tenant_id"],
                "embedding": embedding,
            }

            self.client.index(
                index=INDEX_NAME,
                id=document["id"],
                document=body,
            )

        self.client.indices.refresh(
            index=INDEX_NAME
        )


# 这里发生了什么

"""
注意：

texts = [
    document["content"]
    for document in documents
]

得到：

[
    "Redis 是一个基于内存的高性能键值数据库...",
    "Redis 的 maxmemory-policy 用于控制...",
    "Redis Cluster 通过多个节点...",
    "Java G1 垃圾收集器..."
]

然后：

embeddings = embedding_service.embed_batch(texts)

得到：

[
    [512 dimensions],
    [512 dimensions],
    [512 dimensions],
    [512 dimensions]
]

最后写入：

Elasticsearch

"""
