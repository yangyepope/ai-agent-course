from elasticsearch import Elasticsearch


class ElasticsearchClient:

    def __init__(
        self,
        url: str = "http://127.0.0.1:9200",
    ):
        self.client = Elasticsearch(url)

    def get_client(self) -> Elasticsearch:
        return self.client

    def ping(self) -> bool:
        return self.client.ping()


# 调试代码

es = ElasticsearchClient()

print(es.ping())
