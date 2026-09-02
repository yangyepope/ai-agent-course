"""
RRF 结果融合器（Reciprocal Rank Fusion，倒数排名融合）——Hybrid Search 的"合榜"环节。

作用：
    把多个检索器（语义检索 vector_store.py、关键词检索 keyword_search.py）
    各自返回的 Top-K 结果，合并成【一份统一排名】的结果列表。
    只认"排名"、不认"分数"——这是 RRF 与"分数加权求和"最根本的区别。

为什么需要它（Hybrid Search 为什么要"合榜"）：
    两个检索器用的打分体系完全不同：
        - vector_store 的 score 是余弦相似度，范围约 0~1；
        - keyword_search 的 score 是 BM25 分值，没有固定上限，量级能差出好几个数量级。
    所以"直接把两边分数相加"没有意义（量纲不一致）。
    RRF 的解法：丢掉原始分数，只看"你在你那一榜里排第几"，
    再用公式 1 / (k + rank) 把名次折算成一个可比的小分数，跨榜累加，
    从而让两边的贡献是"公平"的。

核心公式：
    RRF_score(d) = Σ_榜单  1 / (k + rank_d)
        其中 rank_d 是文档 d 在该榜里的名次（从 1 开始），k 是平滑常数（rrf_k）。
    含义：
        - 排名越靠前，单榜得分越大（rank=1 时得 1/(k+1)）；
        - 只有一面榜单出现（比如只有语义检索命中）的文档，
          得分 = 单个来源的 1/(k+rank)；
        - 两边都命中的文档，两边分数累加，天然更容易排到前面——
          这正是混合检索想要的效果："证据"越多越靠前。

在 Hybrid RAG 链路中的位置：
    语义检索(vector_store)  ┐
                           ├→ RRF 融合(fusion.py)
    关键词检索(keyword_search) ┘
    融合结果 → Reranker 精排(reranker.py) → Retriever 统一入口 → LLM
"""


class RRFFusion:
    """
    一个极简的 RRF（倒数排名融合）实现。

    与上游检索器的接口约定：
        入参是"多个榜单"（list[list[dict]]），每个榜单里的每个元素形如
            {
                "document": Document,  # 文档切片对象（用 document.id 作为唯一标识）
                "score":    float,     # 该榜的原始分数（RRF 故意不用它）
                "rank":     int,       # 该榜内的名次，从 1 开始（RRF 只认它）
            }
        ——这正是 VectorStore.search / KeywordSearch.search 的返回结构，
          把两边结果直接拼成列表传进来即可。

    输出结构：
        融合后的"一份榜单"：list[dict]，结构与上游完全一致，
        已按 RRF 总分从高到低排好，并重新生成了从 1 开始的新 rank。
    """

    def __init__(
        self,
        rrf_k: int = 60,
    ):
        """初始化：保存 RRF 的平滑常数 k。

        参数说明：
            rrf_k: 公式 1/(k + rank) 里的平滑常数，默认 60（学术论文与
                   Elasticsearch 的推荐默认值）。

                   k 的作用是"调节名次差异的敏感度"：
                       k 越大 -> 第 1 名和第 10 名的得分差距越小，
                                榜单整体越"平均主义"，两头都不突出；
                       k 越小 -> 越强调各榜的前几名，第一名拿到的权重占比越大。
                   实践中默认 60 通常表现稳定，无需频繁调整。
        """
        self.rrf_k = rrf_k

    def fuse(
        self,
        result_lists: list[list[dict]],
    ) -> list[dict]:
        """融合：输入多个检索榜单，输出一份按 RRF 总分排序的统一榜单。

        参数说明：
            result_lists: 多个榜单的列表。每个榜单是一个 list[dict]，
                          来自一次检索（如向量检索的结果、BM25 检索的结果），
                          榜单内元素形如：
                          {"document": Document, "score": float, "rank": int}，
                         允许传入 1 个或 2 个（甚至更多）榜单。

        返回：list[dict]，一份融合后的榜单，每个元素形如
            {
                "document": Document,  # 命中的文档切片对象
                "score":    float,     # RRF 融合总分（= 各榜 1/(k+rank) 之和，越大越靠前）
                "rank":     int,       # 融合后的新排名，从 1 开始
            }
            按 RRF 总分从高到低排列。

        算法分三步：
            1. 遍历所有榜单、所有结果，把每条的排名折算成 RRF 分数，
               按 document.id 累加（同一文档在多个榜单都出现就累加）；
            2. 按累加后的总分从高到低排序；
            3. 按新顺序重排结果，并生成从 1 开始的新 rank。
        """

        # ---- 第 1 步：跨榜单按 document.id 累加 RRF 分数 ----

        # 累计分账本：document_id -> RRF 总分（默认 0.0，首次命中从 0 累加）
        scores: dict[str, float] = {}

        # 文档对象账本：document_id -> Document 对象（总分排序后要按 id 找回原文）
        documents = {}

        # 遍历"榜单"层：result_lists 的每个元素是一整个榜单（一次检索的全部结果）
        for results in result_lists:

            # 遍历"结果"层：榜单里的每一条命中
            for result in results:

                # 取出命中的文档对象（RRF 的累加单位是"文档"）
                document = result["document"]

                # 取出该文档在这一榜里的名次（从 1 开始，由上游检索器生成）
                rank = result["rank"]

                # 核心公式：名次 -> RRF 分数
                # 排名越靠前（rank 越小），分数越大；k 起平滑作用
                rrf_score = (
                    1.0
                    / (self.rrf_k + rank)
                )

                # 用 document.id 作为跨榜单识别的唯一键
                # （两榜返回的是同一批 Document 对象时 id 一致，分数才能正确累加）
                document_id = document.id

                # 累加：该文档若已被其他榜单计过分，就在旧分基础上加；
                # scores.get(document_id, 0.0) 保证第一次出现时从 0 开始
                scores[document_id] = (
                    scores.get(
                        document_id,
                        0.0,
                    )
                    + rrf_score
                )

                # 顺手记下文档对象本身（只记最后一次即可，同一 id 对应同一个对象）
                documents[
                    document_id
                ] = document

        # ---- 第 2 步：按 RRF 总分从高到低排序 ----
        # scores.items() 得到 [(document_id, 总分), ...]
        # key=lambda item: item[1] 表示按"总分"排序，reverse=True 高分的在前
        sorted_documents = sorted(
            scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        # ---- 第 3 步：重排结果，生成从 1 开始的新 rank ----
        # 上游榜单各自的 rank 已经失效（那是"榜内名次"），
        # 融合后必须按总分重新生成一份全局名次
        results = []

        # enumerate(sorted_documents, start=1) 顺带生成新排名：
        # sorted_documents 里每个元素是 (document_id, 总分)
        for rank, (
            document_id,
            score,
        ) in enumerate(
            sorted_documents,
            start=1,
        ):

            # 组装成与上游检索器相同的返回结构，方便上层无差别消费
            # "score" 是 RRF 融合总分，"rank" 是融合后的全局新名次
            results.append(
                {
                    "document": documents[
                        document_id
                    ],
                    "score": score,
                    "rank": rank,
                }
            )

        # 返回一份统一的、按相关度从高到低排列的融合榜单
        return results
