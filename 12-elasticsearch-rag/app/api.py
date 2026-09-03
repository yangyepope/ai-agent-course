from app.elasticsearch_client import ElasticsearchClient
from app.embedding import EmbeddingService
from app.search_service import SearchService
from fastapi import APIRouter

router = APIRouter()

es_client = ElasticsearchClient()

embedding_service = EmbeddingService()

search_service = SearchService(
    es_client.get_client()
)


@router.post("/search")
def search(
    query: str,
    tenant_id: str,
    top_k: int = 5,
):

    results = search_service.hybrid_search(
        query=query,
        embedding_service=embedding_service,
        top_k=top_k,
    )

    return {
        "query": query,
        "results": [
            {
                "id": hit["_source"]["chunk_id"],
                "score": hit["_score"],
                "content": hit["_source"]["content"],
                "source": hit["_source"]["source"],
                "page": hit["_source"]["page"],
            }
            for hit in results
        ],
    }
