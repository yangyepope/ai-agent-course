from app.evaluation.dataset import (
    EvaluationDataset,
)
from app.evaluation.metrics import (
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)


class RAGEvaluator:

    def __init__(
        self,
        rag_service,
    ):
        self.rag_service = rag_service

    def evaluate_retrieval(
        self,
        dataset: EvaluationDataset,
        top_k: int = 5,
    ) -> dict:

        recalls = []

        precisions = []

        reciprocal_ranks = []

        details = []

        for case in dataset.cases:

            documents = (
                self.rag_service.retrieve(
                    query=case.question,
                    top_k=top_k,
                )
            )

            retrieved_ids = [
                document["chunk_id"]
                for document in documents
            ]

            relevant_ids = (
                case.relevant_chunks
            )

            recall = recall_at_k(
                retrieved_ids,
                relevant_ids,
                top_k,
            )

            precision = precision_at_k(
                retrieved_ids,
                relevant_ids,
                top_k,
            )

            rr = reciprocal_rank(
                retrieved_ids,
                relevant_ids,
            )

            recalls.append(recall)

            precisions.append(precision)

            reciprocal_ranks.append(rr)

            details.append(
                {
                    "id": case.id,
                    "question": case.question,
                    "retrieved_ids": retrieved_ids,
                    "relevant_ids": relevant_ids,
                    "recall": recall,
                    "precision": precision,
                    "reciprocal_rank": rr,
                }
            )

        count = len(
            dataset.cases
        )

        return {
            "recall_at_k": (
                sum(recalls) / count
            ),
            "precision_at_k": (
                sum(precisions) / count
            ),
            "mrr": (
                sum(reciprocal_ranks)
                / count
            ),
            "details": details,
        }
