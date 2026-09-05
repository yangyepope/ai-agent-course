from app.evaluation.dataset import (
    EvaluationDataset,
)
from app.evaluation.evaluator import (
    RAGEvaluator,
)
from app.evaluation.report import (
    EvaluationReport,
)
from app.rag.service import (
    RAGService,
)
from app.retrieval.mock_retriever import (
    MockRetriever,
)


class SimpleReranker:

    def rerank(
        self,
        query: str,
        documents: list[dict],
        top_k: int,
    ) -> list[dict]:

        return documents[:top_k]


def create_rag_service() -> RAGService:

    retriever = MockRetriever()

    reranker = SimpleReranker()

    return RAGService(
        retriever=retriever,
        reranker=reranker,
        llm=None,
    )

import json


def save_result(
    result: dict,
    path: str,
):

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            result,
            file,
            ensure_ascii=False,
            indent=2,
        )





def main():

    dataset = EvaluationDataset.load(
        "data/evaluation_dataset.json"
    )

    # save_result(



    rag_service = create_rag_service()

    evaluator = RAGEvaluator(
        rag_service=rag_service
    )

    metrics = evaluator.evaluate_retrieval(
        dataset=dataset,
        top_k=5,
    )

    save_result(
    metrics,
    "data/evaluation_result.json",
)

    report = EvaluationReport(
        dataset_size=len(dataset)
    )

    report.add(
        "Recall@5",
        metrics["recall_at_k"],
    )

    report.add(
        "Precision@5",
        metrics["precision_at_k"],
    )

    report.add(
        "MRR",
        metrics["mrr"],
    )

    report.print()


if __name__ == "__main__":
    main()
