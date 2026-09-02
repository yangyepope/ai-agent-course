# from app.config import load_documents
# from app.embeddings import EmbeddingService
# from app.vector_store import VectorStore
# from app.keyword_search import KeywordSearch
# from app.fusion import RRFFusion


# def print_results(
#     title: str,
#     results: list[dict],
# ):

#     print()
#     print("=" * 80)
#     print(title)
#     print("=" * 80)

#     for result in results:

#         document = result["document"]

#         print(
#             f"""
#                 Rank     : {result["rank"]}
#                 Score    : {result["score"]:.4f}
#                 ID       : {document.id}
#                 Source   : {document.source}
#                 Page     : {document.page}
#                 Category : {document.category}
#                 Content  : {document.content}
#             """
#         )

# def main():

#     documents = load_documents()

#     embedding_service = EmbeddingService()

#     vector_store = VectorStore(
#         documents,
#         embedding_service,
#     )

#     keyword_search = KeywordSearch(
#         documents
#     )

#     query = "Redis maxmemory-policy 是干什么的？"

#     vector_results = vector_store.search(
#         query,
#         k=5,
#     )

#     keyword_results = keyword_search.search(
#         query,
#         k=5,
#     )

#     print_results(
#         "VECTOR SEARCH",
#         vector_results,
#     )

#     print_results(
#         "BM25 SEARCH",
#         keyword_results,
#     )
    
#     fusion = RRFFusion()
    
#     fused_results = fusion.fuse([
#       vector_results,
#       keyword_results,  
#     ])
    
#     """ 
#     Query
#     │
#     ├───────────────┐
#     ▼               ▼
#     Vector          BM25
#     │               │
#     ▼               ▼
#     Top 5           Top 5
#     │               │
#     └───────┬───────┘
#             ▼
#             RRF
#             │
#             ▼
#     Hybrid Results 
#     """
    
    
#     print_results(  "HYBRID SEARCH / RRF",
#     fused_results,)


# if __name__ == "__main__":
#     main()


from app.config import load_documents
from app.embeddings import EmbeddingService
from app.fusion import RRFFusion
from app.keyword_search import KeywordSearch
from app.reranker import Reranker
from app.retriever import HybridRetriever
from app.vector_store import VectorStore


def main():

    # ==================================================
    # 1. Load Documents
    # ==================================================    

    documents = load_documents()

    # ==================================================
    # 2. Embedding
    # ==================================================

    embedding_service = EmbeddingService()

    # ==================================================
    # 3. Vector Store
    # ==================================================

    vector_store = VectorStore(
        documents=documents,
        embedding_service=embedding_service,
    )

    # ==================================================
    # 4. BM25
    # ==================================================

    keyword_search = KeywordSearch(
        documents=documents
    )

    # ==================================================
    # 5. RRF
    # ==================================================

    fusion = RRFFusion(
        rrf_k=60
    )

    # ==================================================
    # 6. Reranker
    # ==================================================

    reranker = Reranker()

    # ==================================================
    # 7. Hybrid Retriever
    # ==================================================

    retriever = HybridRetriever(
        vector_store=vector_store,
        keyword_search=keyword_search,
        fusion=fusion,
        reranker=reranker,
    )

    # ==================================================
    # 8. Query
    # ==================================================

    query = (
        "Redis maxmemory-policy 是干什么的？"
    )

    # ==================================================
    # 9. Retrieval
    # ==================================================

    results = retriever.retrieve(
        query=query,
        candidate_k=5,
        top_k=3,
    )

    # ==================================================
    # 10. Print
    # ==================================================

    print()
    print("=" * 80)
    print("FINAL RETRIEVAL RESULTS")
    print("=" * 80)

    for result in results:

        document = result["document"]

        print()
        print(
            f"Rank          : {result['rank']}"
        )

        print(
            f"RRF Score     : "
            f"{result['score']:.6f}"
        )

        print(
            f"Rerank Score  : "
            f"{result['rerank_score']:.6f}"
        )

        print(
            f"Document ID   : {document.id}"
        )

        print(
            f"Source        : {document.source}"
        )

        print(
            f"Page          : {document.page}"
        )

        print(
            f"Category      : {document.category}"
        )

        print(
            f"Content       : {document.content}"
        )


if __name__ == "__main__":
    main()