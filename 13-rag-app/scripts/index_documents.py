"""
灌数据。

    python -m scripts.index_documents
    python -m scripts.index_documents data/documents.json

必须在 13-rag-app/ 目录下执行 —— 默认路径是相对路径。
索引不存在会直接报错，先跑 python -m scripts.init_index。
"""

import sys
import time

from app.config import ES_INDEX
from app.document_service import DocumentService
from app.elasticsearch_client import ElasticsearchClient
from app.embedding import EmbeddingService
from app.index_manager import IndexManager
from app.logging_config import setup_logging

DEFAULT_DATA_PATH = "data/documents.json"


def main() -> None:
    setup_logging()

    file_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DATA_PATH

    es_client = ElasticsearchClient()

    if not es_client.ping():
        raise RuntimeError("连不上 Elasticsearch")

    index_manager = IndexManager(es_client.get_client())

    # 不建索引直接写，ES 的 dynamic mapping 会把 embedding
    # 猜成普通 float 数组：写入静默成功，但 kNN 查询会报错。
    # 所以这里挡在前面。
    if not index_manager.exists():
        raise RuntimeError(f"索引 {ES_INDEX} 不存在，请先执行 python -m scripts.init_index")

    print("加载 Embedding 模型…", flush=True)

    document_service = DocumentService(
        client=es_client.get_client(),
        embedding_service=EmbeddingService(),
    )

    documents = document_service.load_documents(file_path)

    print(f"读到 {len(documents)} 条，开始写入 {ES_INDEX}", flush=True)

    started = time.perf_counter()

    total = document_service.index_documents(documents)

    elapsed = time.perf_counter() - started

    print(f"\n完成：{total} 条，耗时 {elapsed:.1f} 秒。索引现有 {index_manager.count()} 条文档。")


if __name__ == "__main__":
    main()
