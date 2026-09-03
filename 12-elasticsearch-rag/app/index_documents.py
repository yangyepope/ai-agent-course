from app.document_service import DocumentService
from app.elasticsearch_client import ElasticsearchClient
from app.embedding import EmbeddingService


def main():

    es_client = ElasticsearchClient()

    embedding_service = EmbeddingService()

    document_service = DocumentService(
        client=es_client.get_client(),
        embedding_service=embedding_service,
    )

    documents = document_service.load_documents(
        "data/documents.json"
    )

    document_service.index_documents(
        documents
    )

    print(
        f"indexed {len(documents)} documents"
    )


if __name__ == "__main__":
    main()
