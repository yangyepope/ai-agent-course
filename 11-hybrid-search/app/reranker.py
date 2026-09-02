"""
交叉编码器精排器（Reranker）——Hybrid Search 的"精排（Rerank）"环节。

作用：
    对上游（如 fusion.py RRF 融合后）给的一批候选结果，用 CrossEncoder
    重新逐条打分排序，把真正相关的文档提到最前面。

为什么"召回（粗排）之后还需要精排（Rerank）"：
    召回阶段（vector_store / keyword_search / fusion）用的是"轻量近似"手段，
    目的是从全库里快速筛出"可能相关"的 Top-K，这个阶段求快、求广，难免混进噪音。
    精排阶段则用更强的模型对【每一条候选】和【用户问题】做一次"仔细比对"，
    把候选里真正贴题的内容挑出来放最前面。

    Reranker 与 Bi-Encoder 的区别（本项目的 embeddings.py 是 Bi-Encoder）：
        - Bi-Encoder（向量检索用）：query 和 doc 各自编码成向量再算相似度。
          优点：文档向量可离线算好缓存，检索快；
          缺点：query 和 doc 在编码阶段"没互相见过"，细粒度交互信息会丢失。
        - CrossEncoder（本文件用的）：把 query 和 doc 拼成一个输入喂给模型，
          让模型在"同一个注意力上下文里"看两者的完整文本，再做相关性打分。
          优点：精度显著更高（业界一般高 3~10 个百分点）；
          缺点：每对 (query, doc) 都要过一遍模型，慢，
                所以只能用来精排"少量候选"，不能直接用来在全库里检索。
    RAG 实践中的标准做法：Bi-Encoder 先召回 Top-50~100，
    CrossEncoder 再精排取 Top-5~10 喂给 LLM——本文件就是后半段。

在 Hybrid RAG 链路中的位置：
    语义检索(vector_store) ┐
                           ├→ RRF 融合(fusion.py) → Reranker 精排(本文件)
    关键词检索(keyword_search) ┘
        → 精排后的 Top-K → Retriever 统一入口 → LLM

技术选型说明：
    - 使用 sentence-transformers 的 CrossEncoder，默认模型 BAAI/bge-reranker-base
      （BGE 系列，中文效果好的轻量 rerank 模型，首次使用会自动从 HuggingFace 下载）；
    - 模型输出的是"相关程度"分数（sigmoid 归一化到 0~1，越大越相关）。
"""

# type: ignore[reportMissingImports]  # 交叉编码器：把 (query, doc) 拼一起做相关性打分
from sentence_transformers import CrossEncoder 


class Reranker:
    """
    一个极简的交叉编码器精排器。

    输入输出约定（与上游 fusion.py / vector_store.py / keyword_search.py 一致）：
        每个结果元素形如
            {
                "document": Document,  # 文档切片对象
                "score":    float,     # 上游给的原始分数（融合分/相似度/BM25）
                "rank":     int,       # 上游榜内的名次（精排后会按新分数覆盖）
                ...                    # 可能还有其他字段
            }
    精排后返回同构的结果列表，但会：
        1. 给每条结果附加 rerank_score（CrossEncoder 打出的精排分）；
        2. 按 rerank_score 重新排序；
        3. 只保留前 top_k 条，并重新生成从 1 开始的新 rank。
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-base",
    ):
        """初始化：加载 CrossEncoder 精排模型。

        参数说明：
            model_name: HuggingFace 上的 rerank 模型名，默认 "BAAI/bge-reranker-base"。
                        首次加载会联网下载模型权重（缓存在本地 ~/.cache 下），
                        之后离线可直接使用。
        """
        # CrossEncoder 与 Bi-Encoder 的关键差异：模型内部会把 (query, document)
        # 拼成一个输入序列一起过 Transformer，从而让两者充分"交互"后再打分
        self.model = CrossEncoder(
            model_name
        )

    def rerank(
        self,
        query: str,
        results: list[dict],
        top_k: int = 5,
    ) -> list[dict]:
        """精排：输入用户问题和一批候选结果，返回按精排分重排后的 Top-K。

        参数说明：
            query:   用户问题（纯文本）。
            results: 上游召回/融合后的候选列表（通常来自 fusion.py 的 RRF 结果），
                     元素形如 {"document": Document, "score": float, "rank": int}。
            top_k:   精排后最多返回几条（最终喂给 LLM 的上下文条数），默认 5。

        返回：list[dict]，精排后的结果列表，元素形如
            {
                "document":      Document,  # 命中的文档切片对象
                "score":         float,     # 上游原始分数（原样保留）
                "rank":          int,       # 新的排名，从 1 开始（已被精排结果覆盖）
                "rerank_score":  float,     # CrossEncoder 打出的精排分（0~1，越大越相关）
                ...                          # 原结果里的其它字段也会被保留
            }
            按 rerank_score 从高到低排列，只保留前 top_k 条。

        算法分四步：
            1. 把每条候选的 (query, 文档正文) 组成打分对；
            2. 用 CrossEncoder 批量打分，得到每条候选的精排分；
            3. 按精排分从高到低排序，截断到 top_k 条；
            4. 重新生成从 1 开始的新 rank（覆盖上游的旧名次）。
        """

        # ---- 边界情况：没有候选就直接返回空，避免空手做无用功 ----
        if not results:
            return []

        # ---- 第 1 步：构造 (query, 文档正文) 打分对 ----
        # CrossEncoder 一次吃"一对文本"，输出这一对的匹配程度；
        # 注意比对的是 document.content（正文）而不是整个 Document 对象
        pairs = []

        for result in results:

            document = result["document"]

            pairs.append(
                (
                    query,
                    document.content,
                )
            )

        # ---- 第 2 步：批量精排打分 ----
        # model.predict(pairs) 返回与 pairs 一一对应的分数列表；
        # 分数含义：bge-reranker 输出经 sigmoid 归一化到 0~1，越大表示与问题越相关
        scores = self.model.predict(
            pairs
        )

        # ---- 第 3 步：把精排分并进原结果，再排序截断 ----
        # {**result, "rerank_score": ...} 是"浅拷贝展开再追加字段"：
        # 保留原结果的所有字段（document / score / rank / ...），
        # 额外塞进一个 rerank_score，不去动原始数据
        reranked = []

        for result, score in zip(
            results,
            scores,
        ):

            reranked.append(
                {
                    **result,
                    "rerank_score": float(score),
                }
            )

        # 按精排分从高到低排序（score 越大越相关，排越前面）
        reranked.sort(
            key=lambda item: item["rerank_score"],
            reverse=True,
        )

        # 只保留前 top_k 条：精排模型算力贵，最终只需喂给 LLM 的少量高质上下文
        reranked = reranked[:top_k]

        # ---- 第 4 步：重新生成从 1 开始的新排名 ----
        # 上游（融合/召回）给的名次基于旧分数，精排换序后已失效，
        # 必须按新顺序覆盖一遍，保证 rank 与最终展示顺序一致
        for rank, result in enumerate(
            reranked,
            start=1,
        ):
            result["rank"] = rank

        # 返回精排后的 Top-K 结果
        return reranked
