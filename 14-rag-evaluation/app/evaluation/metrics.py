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


# NDCG 需要的是"每个位置的相关性分数"，
# 但 dataset 里只有 relevant_chunks 这种 0/1 判断，
# 所以要先把 retrieved_ids 翻译成增益序列。
def build_relevance_scores(
    retrieved_ids: Sequence[str],
    relevant_ids: Sequence[str],
    k: int,
) -> list[int]:

    relevant = set(
        relevant_ids
    )

    scores = [
        1 if doc_id in relevant else 0
        for doc_id in retrieved_ids[:k]
    ]

    # 召回不足时补 0，
    # 保证前 k 位就是真实的检索结果。
    while len(scores) < k:
        scores.append(0)

    # 关键一步：没被召回的相关文档也要记进来。
    # 否则 ndcg_at_k 内部排序算出来的 ideal 会偏小，
    # 导致"漏召回"反而拿到虚高的 NDCG。
    hit_count = sum(scores)

    missed_count = len(relevant) - hit_count

    scores.extend(
        [1] * missed_count
    )

    return scores


# 举例说明为什么要补"漏召回"：
"""
relevant：A、B
retrieved@5：X A X X X

如果只看召回结果：

    [0, 1, 0, 0, 0]

ideal 排序后 = [1, 0, 0, 0, 0]

NDCG = 0.63   ← 虚高，B 完全没召回却没被惩罚

补上漏掉的 B 之后：

    [0, 1, 0, 0, 0, 1]

ideal 排序后 = [1, 1, 0, 0, 0, 0]

NDCG = 0.63 / 1.63 = 0.39   ← 这才是真实水平
"""
