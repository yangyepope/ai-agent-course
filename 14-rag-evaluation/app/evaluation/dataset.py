import json
from dataclasses import dataclass


@dataclass
class EvaluationCase:

    id: str

    question: str

    ground_truth: str

    relevant_chunks: list[str]


class EvaluationDataset:

    def __init__(
        self,
        cases: list[EvaluationCase],
    ):
        self.cases = cases

    @classmethod
    def load(
        cls,
        path: str,
    ) -> "EvaluationDataset":

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        cases = [
            EvaluationCase(
                id=item["id"],
                question=item["question"],
                ground_truth=item["ground_truth"],
                relevant_chunks=item[
                    "relevant_chunks"
                ],
            )
            for item in data
        ]

        return cls(cases)

    def __len__(self):
        return len(self.cases)
