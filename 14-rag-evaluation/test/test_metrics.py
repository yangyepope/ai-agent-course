from app.evaluation.metrics import (
    build_relevance_scores,
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


def test_ndcg_排序变差时降低():

    好排序 = ndcg_at_k(
        [
            1,
            1,
            0,
            0,
        ],
        4,
    )

    坏排序 = ndcg_at_k(
        [
            0,
            0,
            1,
            1,
        ],
        4,
    )

    assert 好排序 == 1.0

    assert 坏排序 < 好排序


def test_build_relevance_scores_命中位置():

    scores = build_relevance_scores(
        [
            "X",
            "A",
            "Y",
        ],
        [
            "A",
        ],
        3,
    )

    assert scores == [0, 1, 0]


def test_build_relevance_scores_补齐漏召回():

    # relevant 有 A、B，但只召回了 A，
    # 漏掉的 B 要补进来，
    # 否则 ideal 偏小、NDCG 虚高。
    scores = build_relevance_scores(
        [
            "X",
            "A",
            "Y",
        ],
        [
            "A",
            "B",
        ],
        3,
    )

    assert scores == [0, 1, 0, 1]

    # 前 3 位没变，所以 actual DCG 不受影响，
    # 但 ideal 变大了 → NDCG 被拉低
    漏召回 = ndcg_at_k(scores, 3)

    全召回 = ndcg_at_k(
        [
            0,
            1,
            1,
        ],
        3,
    )

    assert 漏召回 < 全召回
