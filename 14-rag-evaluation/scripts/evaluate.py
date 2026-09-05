import json

from app.evaluation.dataset import (
    EvaluationDataset,
)
from app.evaluation.evaluator import (
    RAGEvaluator,
)
from app.evaluation.judge import (
    LLMJudge,
)
from app.evaluation.report import (
    EvaluationReport,
)
from app.llm.openai_llm import (
    create_llm,
)
from app.rag.service import (
    RAGService,
)
from app.retrieval.mock_retriever import (
    MockRetriever,
)

TOP_K = 5


class SimpleReranker:

    def rerank(
        self,
        query: str,
        documents: list[dict],
        top_k: int,
    ) -> list[dict]:

        return documents[:top_k]


def create_rag_service(llm) -> RAGService:

    retriever = MockRetriever()

    reranker = SimpleReranker()

    return RAGService(
        retriever=retriever,
        reranker=reranker,
        llm=llm,
    )


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

    # 同一个 LLM 既负责生成 Answer，
    # 也负责当 Judge。
    # 真实项目里建议 Judge 换一个更强的模型，
    # 否则模型会倾向于给自己的答案打高分。
    llm = create_llm()

    rag_service = create_rag_service(llm)

    evaluator = RAGEvaluator(
        rag_service=rag_service,
        judge=LLMJudge(llm=llm),
    )

    result = evaluator.evaluate(
        dataset=dataset,
        top_k=TOP_K,
    )

    save_result(
        result,
        "data/evaluation_result.json",
    )

    report = EvaluationReport(
        dataset_size=len(dataset)
    )

    retrieval = result["retrieval"]

    report.add(
        f"Recall@{TOP_K}",
        retrieval["recall_at_k"],
    )

    report.add(
        f"Precision@{TOP_K}",
        retrieval["precision_at_k"],
    )

    report.add(
        "MRR",
        retrieval["mrr"],
    )

    report.add(
        f"NDCG@{TOP_K}",
        retrieval["ndcg_at_k"],
    )

    generation = result["generation"]

    if generation is not None:

        report.add(
            "Answer Relevance",
            generation["answer_relevance"],
            section="Generation",
        )

        report.add(
            "Faithfulness",
            generation["faithfulness"],
            section="Generation",
        )

        report.add(
            "Correctness",
            generation["correctness"],
            section="Generation",
        )

    report.print()


if __name__ == "__main__":
    main()
