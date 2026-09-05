from collections import defaultdict


def reciprocal_rank_fusion(
    result_lists,
    k: int = 60,
):
    """
    result_lists:
        [
            [doc1, doc2, doc3],
            [doc2, doc3, doc4],
        ]
    """

    scores = defaultdict(float)

    documents = {}

    for results in result_lists:

        for rank, document in enumerate(
            results,
            start=1,
        ):

            document_id = (
                document.metadata.get(
                    "chunk_id"
                )
                or document.content
            )

            scores[document_id] += (
                1.0
                / (k + rank)
            )

            documents[
                document_id
            ] = document

    # 注意不能写 key=scores.get。
    # dict.get 的返回类型是 float | None，
    # 而 None 不能比大小，类型检查会报错。
    # 这里排的就是 scores 自己的 key，必然存在，
    # 所以用 [] 取值 —— 返回类型是干净的 float。
    ranked_ids = sorted(
        scores,
        key=lambda document_id: scores[
            document_id
        ],
        reverse=True,
    )

    return [
        documents[document_id]
        for document_id in ranked_ids
    ]
