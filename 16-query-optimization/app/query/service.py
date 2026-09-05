from app.query.base import (
    BaseQueryTransformer,
    Query,
)
from app.retrieval.retriever import (
    RetrievalResult,
    Retriever,
)


class QueryRetrievalService:

    def __init__(
        self,
        transformer: BaseQueryTransformer,
        retriever: Retriever,
    ):

        self.transformer = transformer
        self.retriever = retriever

    def search(
        self,
        query: Query,
        top_k: int = 5,
    ) -> list[RetrievalResult]:

        transformed_queries = (
            self.transformer.transform(
                query
            )
        )

        all_results = []

        for transformed_query in (
            transformed_queries
        ):

            results = self.retriever.search(
                transformed_query.text,
                top_k=top_k,
            )

            all_results.extend(
                results
            )

        return self._deduplicate(
            all_results
        )

    def _deduplicate(
        self,
        results: list[RetrievalResult],
    ) -> list[RetrievalResult]:

        seen = set()

        unique_results = []

        for result in results:

            document_id = (
                result.metadata.get(
                    "chunk_id"
                )
                or result.content
            )

            if document_id in seen:
                continue

            seen.add(document_id)

            unique_results.append(
                result
            )

        return unique_results
