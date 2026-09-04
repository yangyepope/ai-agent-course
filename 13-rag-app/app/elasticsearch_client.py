from app.config import ES_URL
from elasticsearch import Elasticsearch


class ElasticsearchClient:
    def __init__(self):
        self.client = Elasticsearch(ES_URL)

    def ping(self) -> bool:
        return self.client.ping()

    def get_client(self) -> Elasticsearch:
        return self.client


if __name__ == "__main__":
    client = ElasticsearchClient()
    print(client.ping())
