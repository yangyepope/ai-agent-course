"""
写入层：读语料文件 → 批量向量化 → 写入 Elasticsearch。

只在离线阶段跑（index_documents.py），跟在线检索服务是两条独立的路。
"""

import json

from app.config import ES_INDEX
from app.embedding import EmbeddingService
from elasticsearch import Elasticsearch, helpers


class DocumentService:
    def __init__(
        self,
        client: Elasticsearch,
        embedding_service: EmbeddingService,
    ):
        self.client = client
        self.embedding_service = embedding_service

    def load_documents(self, file_path: str) -> list[dict]:
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)

    def index_documents(
        self,
        documents: list[dict],
        batch_size: int = 32,
    ) -> int:
        """
        写入并返回成功条数。

        分批做两件事：
            1. embed_batch 批量算向量（比逐条快得多）
            2. helpers.bulk 批量写 ES（一次请求发一批，
               比逐条 client.index() 快几十倍）

        用 chunk 的 id 当 ES 的 _id，所以重复跑是覆盖而不是
        产生重复文档 —— 脚本可以放心重跑。
        """

        total = 0

        for start in range(0, len(documents), batch_size):
            batch = documents[start : start + batch_size]

            embeddings = self.embedding_service.embed_batch(
                [document["content"] for document in batch]
            )

            actions = [
                {
                    "_index": ES_INDEX,
                    "_id": document["id"],
                    "_source": {
                        "chunk_id": document["id"],
                        "content": document["content"],
                        "source": document["source"],
                        "page": document["page"],
                        "category": document["category"],
                        "tenant_id": document["tenant_id"],
                        "embedding": embedding,
                    },
                }
                for document, embedding in zip(batch, embeddings)
            ]

            success, _ = helpers.bulk(self.client, actions)

            total += int(success)

            print(
                f"  已写入 {total}/{len(documents)}",
                flush=True,
            )

        # ES 默认一秒才刷新一次，不刷的话灌完立刻搜是搜不到的
        self.client.indices.refresh(index=ES_INDEX)

        return total
