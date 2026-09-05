from app.evaluation.metrics import (
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)


def test_recall_at_k():

    retrieved = [
        "A",
        "B",
        "C",
        "D",
    ]

    relevant = [
        "A",
        "C",
    ]

    score = recall_at_k(
        retrieved,
        relevant,
        4,
    )

    assert score == 1.0


def test_precision_at_k():

    retrieved = [
        "A",
        "B",
        "C",
        "D",
    ]

    relevant = [
        "A",
        "C",
    ]

    score = precision_at_k(
        retrieved,
        relevant,
        4,
    )

    assert score == 0.5


def test_reciprocal_rank():

    retrieved = [
        "X",
        "Y",
        "A",
        "B",
    ]

    relevant = [
        "A",
    ]

    score = reciprocal_rank(
        retrieved,
        relevant,
    )

    assert score == 1 / 3


def test_ndcg():

    score = ndcg_at_k(
        [
            3,
            2,
            1,
            0,
        ],
        4,
    )

    assert score == 1.0
