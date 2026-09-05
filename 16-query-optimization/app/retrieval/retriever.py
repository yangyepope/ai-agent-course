from dataclasses import dataclass
from typing import Protocol


@dataclass
class RetrievalResult:

    content: str

    score: float

    metadata: dict


class Retriever(Protocol):

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        ...
