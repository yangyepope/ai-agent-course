from app.evaluation.dataset import (
    EvaluationDataset,
)
from app.evaluation.judge import (
    LLMJudge,
)
from app.evaluation.metrics import (
    build_relevance_scores,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)


class RAGEvaluator:

    def __init__(
        self,
        rag_service,
        judge: LLMJudge | None = None,
    ):
        self.rag_service = rag_service

        # 只评检索时可以不传 judge，
        # 这样不需要 LLM 也能跑。
        self.judge = judge

    # ==============================
    # 第一段：检索质量
    # Recall / Precision / MRR / NDCG
    # ==============================
    def evaluate_retrieval(
        self,
        dataset: EvaluationDataset,
        top_k: int = 5,
    ) -> dict:

        recalls = []

        precisions = []

        reciprocal_ranks = []

        ndcgs = []

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

            # Recall / Precision 只关心"收了多少"，
            # NDCG 才关心"排得对不对"。
            relevance_scores = (
                build_relevance_scores(
                    retrieved_ids,
                    relevant_ids,
                    top_k,
                )
            )

            ndcg = ndcg_at_k(
                relevance_scores,
                top_k,
            )

            recalls.append(recall)

            precisions.append(precision)

            reciprocal_ranks.append(rr)

            ndcgs.append(ndcg)

            details.append(
                {
                    "id": case.id,
                    "question": case.question,
                    "retrieved_ids": retrieved_ids,
                    "relevant_ids": relevant_ids,
                    "recall": recall,
                    "precision": precision,
                    "reciprocal_rank": rr,
                    "ndcg": ndcg,
                }
            )

        count = len(
            dataset.cases
        )

        if count == 0:
            return {
                "recall_at_k": 0.0,
                "precision_at_k": 0.0,
                "mrr": 0.0,
                "ndcg_at_k": 0.0,
                "details": [],
            }

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
            "ndcg_at_k": (
                sum(ndcgs) / count
            ),
            "details": details,
        }

    # ==============================
    # 第二段：生成质量
    # Relevance / Faithfulness / Correctness
    # 这三个没有标准答案可以对字符串，
    # 只能交给 LLM Judge 打分。
    # ==============================
    def evaluate_generation(
        self,
        dataset: EvaluationDataset,
        top_k: int = 5,
    ) -> dict:

        if self.judge is None:
            raise ValueError(
                "evaluate_generation 需要传入 judge"
            )

        relevances = []

        faithfulnesses = []

        correctnesses = []

        details = []

        for case in dataset.cases:

            result = self.rag_service.answer(
                query=case.question,
                top_k=top_k,
            )

            answer = result["answer"]

            documents = result["documents"]

            # Faithfulness 判的是"答案有没有超出 Context"，
            # 所以这里的 context 必须和喂给 LLM 的完全一致。
            context = "\n\n".join(
                document["content"]
                for document in documents
            )

            scores = self.judge.evaluate(
                question=case.question,
                context=context,
                answer=answer,
                ground_truth=case.ground_truth,
            )

            relevance = float(
                scores.get(
                    "answer_relevance",
                    0.0,
                )
            )

            faithfulness = float(
                scores.get(
                    "faithfulness",
                    0.0,
                )
            )

            correctness = float(
                scores.get(
                    "correctness",
                    0.0,
                )
            )

            relevances.append(relevance)

            faithfulnesses.append(
                faithfulness
            )

            correctnesses.append(
                correctness
            )

            details.append(
                {
                    "id": case.id,
                    "question": case.question,
                    "answer": answer,
                    "ground_truth": case.ground_truth,
                    "answer_relevance": relevance,
                    "faithfulness": faithfulness,
                    "correctness": correctness,
                    "reason": scores.get(
                        "reason",
                        "",
                    ),
                }
            )

        count = len(
            dataset.cases
        )

        if count == 0:
            return {
                "answer_relevance": 0.0,
                "faithfulness": 0.0,
                "correctness": 0.0,
                "details": [],
            }

        return {
            "answer_relevance": (
                sum(relevances) / count
            ),
            "faithfulness": (
                sum(faithfulnesses) / count
            ),
            "correctness": (
                sum(correctnesses) / count
            ),
            "details": details,
        }

    # ==============================
    # 完整 Pipeline
    # ==============================
    def evaluate(
        self,
        dataset: EvaluationDataset,
        top_k: int = 5,
    ) -> dict:

        retrieval = self.evaluate_retrieval(
            dataset=dataset,
            top_k=top_k,
        )

        generation = None

        if self.judge is not None:

            generation = (
                self.evaluate_generation(
                    dataset=dataset,
                    top_k=top_k,
                )
            )

        return {
            "retrieval": retrieval,
            "generation": generation,
        }
