from dataclasses import dataclass


@dataclass
class SearchQuery:

    text: str

    source: str

    weight: float = 1.0
