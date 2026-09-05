from typing import Sequence


#先实现Recall
def recall_at_k(
    retrieved_ids: Sequence[str],
    relevant_ids: Sequence[str],
    k: int,
) -> float:

    if not relevant_ids:
        return 0.0

    retrieved = set(
        retrieved_ids[:k]
    )

    relevant = set(
        relevant_ids
    )

    hit_count = len(
        retrieved & relevant
    )

    return hit_count / len(
        relevant
    )

# 计算如下：

"""
例如：

Relevant：

A
B
C

RAG：

A
D
E
F
G

那么：

Recall@5
=
1 / 3
=
0.3333
"""



# 继续实现Precision@K
def precision_at_k(
    retrieved_ids: Sequence[str],
    relevant_ids: Sequence[str],
    k: int,
) -> float:

    if k <= 0:
        return 0.0

    retrieved = retrieved_ids[:k]

    if not retrieved:
        return 0.0

    relevant = set(
        relevant_ids
    )

    hit_count = sum(
        1
        for doc_id in retrieved
        if doc_id in relevant
    )

    return hit_count / len(
        retrieved
    )

# precision_at_k 计算如下：
"""
例如：

Relevant：

A
B
C

RAG：

A
D
E
F
G

而：

Precision@5
=
1 / 5
=
0.2

"""


# 继续实现 MRR

def reciprocal_rank(
    retrieved_ids: Sequence[str],
    relevant_ids: Sequence[str],
) -> float:

    relevant = set(
        relevant_ids
    )

    for rank, doc_id in enumerate(
        retrieved_ids,
        start=1,
    ):

        if doc_id in relevant:
            return 1.0 / rank

    return 0.0


#倒数排名

"""
例如：
Relevant：

C
D
X
Y

RAG：

A
B
C
D

其中：

C

是第一个正确答案。

那么：

RR = 1 / 3
"""


#
"""
一句话记：recall/precision 是"收了多少"，
RR 是"排得多前"。D 虽然被正确召回（recall 给它记一功），
但它是"第二答案"，RR 认为它对"第一个答案排第几"毫无贡献——因为它排在 C 后面，
本来就不影响 LLM 能不能看到正确答案。

"""


import math


def dcg_at_k(
    relevance_scores: list[int],
    k: int,
) -> float:

    scores = relevance_scores[:k]

    total = 0.0

    for index, relevance in enumerate(
        scores,
        start=1,
    ):

        gain = (
            2 ** relevance
        ) - 1

        discount = math.log2(
            index + 1
        )

        total += (
            gain / discount
        )

    return total



# 整个结果排序是否合理
def ndcg_at_k(
    relevance_scores: list[int],
    k: int,
) -> float:

    actual = dcg_at_k(
        relevance_scores,
        k,
    )

    ideal_scores = sorted(
        relevance_scores,
        reverse=True,
    )

    ideal = dcg_at_k(
        ideal_scores,
        k,
    )

    if ideal == 0:
        return 0.0

    return actual / ideal

# 示例如下：
"""
例如：

正确排序：

3
2
1
0

那么：

NDCG = 1.0

如果：

实际排序：

0
1
3
2

NDCG 就会降低。
"""
