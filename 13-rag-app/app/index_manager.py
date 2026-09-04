"""
索引层：定义 mapping、创建索引。

这份 mapping 是「写方」和「读方」之间的契约：
    document_service.py  按它写字段
    retriever.py         按它查字段
两边只要有一个字段名或类型对不上，ES 不会报错，只会静默搜不到。
"""

from app.config import ES_INDEX
from elasticsearch import Elasticsearch

# 与 embedding.py 里的模型对应：
#     bge-small-zh-v1.5 → 512
#     bge-base-zh       → 768
#     bge-large-zh      → 1024
# 换模型必须同时改这里，并且重建索引（dims 不可原地修改）
EMBEDDING_DIMS = 512


class IndexManager:
    def __init__(self, client: Elasticsearch):
        self.client = client

    def exists(self) -> bool:
        return bool(self.client.indices.exists(index=ES_INDEX))

    def create_index(self, recreate: bool = False) -> bool:
        """
        建索引。返回 True 表示这次真的建了。

        recreate=True 会先删掉已有索引，连数据一起删。
        改了 mapping 想生效只能走这条路 —— ES 的 mapping
        不支持原地修改已有字段的类型。
        """

        if self.exists():
            if not recreate:
                return False

            self.client.indices.delete(index=ES_INDEX)

        mappings = {
            "properties": {
                # 用来「筛」的字段一律 keyword：不分词、精确匹配
                "chunk_id": {"type": "keyword"},
                "source": {"type": "keyword"},
                "category": {"type": "keyword"},
                "tenant_id": {"type": "keyword"},
                # 数值，可做范围查询
                "page": {"type": "integer"},
                # 用来「搜」的字段是 text：分词、建倒排索引 → BM25
                #
                # 没装 IK 分词器时，默认分词器把中文切成单字，
                # BM25 精度会明显变差。装了 IK 之后在这里加：
                #     "analyzer": "ik_max_word",
                #     "search_analyzer": "ik_smart",
                # 改完要重建索引。
                "content": {"type": "text"},
                # 向量字段：建 HNSW 图 → kNN
                #
                # similarity 用 cosine，与 embedding.py 里的
                # normalize_embeddings=True 配套：归一化后
                # 余弦相似度等价于点积，算得更快也更稳。
                "embedding": {
                    "type": "dense_vector",
                    "dims": EMBEDDING_DIMS,
                    "index": True,
                    "similarity": "cosine",
                },
            }
        }

        self.client.indices.create(
            index=ES_INDEX,
            mappings=mappings,
        )

        return True

    def count(self) -> int:
        if not self.exists():
            return 0

        response = self.client.count(index=ES_INDEX)

        return int(response["count"])
