"""
精排器（Reranker）—— 接在 ES 混合检索之后的最后一道排序。

与第 11 课 reranker.py 的区别：
    第 11 课吃的是自己封装的 {"document": Document, "score", "rank"}；
    这里吃的是 Elasticsearch 原样返回的 hit，即 {"_source": {...}, "_score": ...}，
    所以取正文的路径是 hit["_source"]["content"]，不是 result["document"].content。

为什么 ES 做完 RRF 还要这一步：
    RRF 只看名次（score = Σ 1/(60 + rank)），压根不知道文档在讲什么。
    CrossEncoder 会把 query 和文档正文拼成一个输入喂给模型，
    在同一个注意力上下文里做细粒度比对，精度显著更高。

    ES 不跑这个模型（ES 是检索引擎，不是模型推理引擎），
    所以这一步在 Python 进程里做。
"""

from sentence_transformers import CrossEncoder


class Reranker:

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-base",
    ):
        self.model_name = model_name

        # 懒加载：这个模型约 1.1GB，进程启动时不加载，
        # 等第一次真的要精排了再加载，避免 uvicorn 启动卡住
        self.model: CrossEncoder | None = None

    def _load_model(self) -> CrossEncoder:

        if self.model is None:
            self.model = CrossEncoder(
                self.model_name
            )

        return self.model

    def rerank(
        self,
        query: str,
        hits: list[dict],
        top_k: int = 5,
    ) -> list[dict]:
        """
        输入：ES 返回的 hits（每条形如 {"_source": {...}, "_score": ...}）
        输出：同构的 hits，但每条多一个 _rerank_score，
              并按它从高到低排序、截断到 top_k 条。

        原始的 _score（RRF 融合分）原样保留，方便对比精排前后的名次变化。
        """

        if not hits:
            return []

        model = self._load_model()

        # 第 1 步：构造 (query, 文档正文) 打分对
        pairs = [
            (
                query,
                hit["_source"]["content"],
            )
            for hit in hits
        ]

        # 第 2 步：批量打分。每一对都要过一遍模型，所以候选不能太多
        scores = model.predict(pairs)

        # 第 3 步：把精排分并进原 hit（浅拷贝，不改原数据）
        reranked = [
            {
                **hit,
                "_rerank_score": float(score),
            }
            for hit, score in zip(hits, scores)
        ]

        # 第 4 步：按精排分排序，截断
        reranked.sort(
            key=lambda hit: hit["_rerank_score"],
            reverse=True,
        )

        return reranked[:top_k]
