import math
from collections.abc import Sequence


def cosine_similarity(
    a: Sequence[float],
    b: Sequence[float],
) -> float:

    dot_product = sum(
        x * y
        for x, y in zip(a, b)
    )

    norm_a = math.sqrt(
        sum(x * x for x in a)
    )

    norm_b = math.sqrt(
        sum(x * x for x in b)
    )

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (
        norm_a * norm_b
    )


a = [1, 0]

b = [0.9, 0.1]

c = [-1, 0]


print(
    cosine_similarity(a, b)
)

print(
    cosine_similarity(a, c)
)   


# 0.9938837346736189
# -1.0