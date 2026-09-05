from dataclasses import dataclass


@dataclass
class QueryExperiment:

    name: str

    strategy: str

    query_count: int = 1

    top_k: int = 5


"""
experiments = [

    QueryExperiment(
        name="baseline",
        strategy="original",
        query_count=1,
    ),

    QueryExperiment(
        name="rewrite",
        strategy="rewrite",
        query_count=1,
    ),

    QueryExperiment(
        name="multi-query-3",
        strategy="multi_query",
        query_count=3,
    ),

    QueryExperiment(
        name="multi-query-5",
        strategy="multi_query",
        query_count=5,
    ),

    QueryExperiment(
        name="hyde",
        strategy="hyde",
        query_count=1,
    ),
]
"""
