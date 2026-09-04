"""
建索引。跑一次就行。

    python -m scripts.init_index              # 已存在则跳过
    python -m scripts.init_index --recreate   # 先删再建（数据一起删）

改了 index_manager.py 里的 mapping 或 EMBEDDING_DIMS 之后，
必须带 --recreate 才会生效 —— ES 的 mapping 不支持原地修改。
"""

import sys

from app.config import ES_INDEX, ES_URL
from app.elasticsearch_client import ElasticsearchClient
from app.index_manager import EMBEDDING_DIMS, IndexManager
from app.logging_config import setup_logging


def main() -> None:
    setup_logging()

    recreate = "--recreate" in sys.argv

    es_client = ElasticsearchClient()

    # 先探活，ES 没起来时给一句人话而不是一堆连接超时堆栈
    if not es_client.ping():
        raise RuntimeError(f"连不上 Elasticsearch: {ES_URL}")

    index_manager = IndexManager(es_client.get_client())

    existed = index_manager.exists()

    created = index_manager.create_index(recreate=recreate)

    if created and existed:
        print(f"索引 {ES_INDEX} 已删除并重建（dims={EMBEDDING_DIMS}）")
    elif created:
        print(f"索引 {ES_INDEX} 创建完成（dims={EMBEDDING_DIMS}）")
    else:
        print(
            f"索引 {ES_INDEX} 已存在，跳过。"
            f"当前 {index_manager.count()} 条文档。\n"
            f"想改 mapping 请加 --recreate"
        )


if __name__ == "__main__":
    main()
