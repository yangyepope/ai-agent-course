from app.elasticsearch_client import ElasticsearchClient
from app.index_manager import IndexManager


def main():

    es_client = ElasticsearchClient()

    if not es_client.ping():
        raise RuntimeError(
            "Elasticsearch connection failed"
        )

    index_manager = IndexManager(
        es_client.get_client()
    )

    index_manager.create_index()

    print("index created")


if __name__ == "__main__":
    main()

# 测试命令
#  curl -s --noproxy '*' http://127.0.0.1:9200/rag_chunks
