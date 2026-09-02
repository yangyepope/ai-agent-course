"""
混合检索器（HybridRetriever）——整条 Hybrid Search 管线的"统一入口"。

作用：
    把前面所有环节串成一条完整的检索流水线，对外只暴露一个 retrieve() 方法：
        VectorStore(语义召回) ┐
                              ├→ RRFFusion(RRF 融合) → Reranker 精排 → 最终 Top-K
                              KeywordSearch(BM25召回) ┘
    调用方（main / 问答链路）不需要知道底下用了几个检索器、
    怎么融合、怎么精排——这些细节全部收拢在本文件里。

为什么需要这样一个"入口"：
    前面的 vector_store / keyword_search / fusion / reranker 是四个独立零件，
    各自都能单独用，但如果每次都让上层自己拼装，会有一堆重复代码，
    还容易拼错顺序。HybridRetriever 把"标准拼装方式"固化成一个类：
        - 构造时注入四个零件（依赖注入，零件可以随时替换成别的实现）；
        - 使用时只调 retrieve(query)，即可拿到最终结果。

本文件串联的完整流程（对应 main.py 目前手写的那几段，最终应替换成它）：
    Query
      ├─→ VectorStore.search(k=candidate_k)   ① 语义召回（粗）
      ├─→ KeywordSearch.search(k=candidate_k)  ② 关键词召回（粗）
      └─→ RRFFusion.fuse([向量结果, BM25结果]) ③ 融合成一份统一榜单
           └─→ Reranker.rerank(top_k=top_k)    ④ 交叉编码器精排，取最相关的少量结果
"""

from app.fusion import RRFFusion  # RRF 融合器：把多路榜单合成一份
from app.keyword_search import KeywordSearch  # BM25 关键词检索器
from app.reranker import Reranker  # CrossEncoder 精排器
from app.vector_store import VectorStore  # FAISS 向量检索器


class HybridRetriever:
    """
    一个"编排型"的检索器：自己不干活，只负责按正确顺序调度四个零件。

    设计思想：
        - 构造时通过依赖注入把四个零件收进来（而不是在内部自己 new），
          好处是零件可以被替换/复用（比如换成别的向量库、别的精排模型）；
        - 对外只暴露 retrieve()，上层完全感知不到"混合检索"的存在，
          用起来和 10 课的普通 Retriever 一样简单。
    """

    def __init__(
        self,
        vector_store: VectorStore,
        keyword_search: KeywordSearch,
        fusion: RRFFusion,
        reranker: Reranker,
    ):
        """初始化：注入四个零件实例。

        参数说明：
            vector_store:   向量检索器（已建好 FAISS 索引），负责语义召回
            keyword_search: BM25 关键词检索器（已建好 BM25 索引），负责字面召回
            fusion:         RRF 融合器，负责把两路榜单合成一份
            reranker:       CrossEncoder 精排器，负责对融合结果做最终精排

        四个零件都需要用【同一批】 documents 分别构造（vector_store 和
        keyword_search 的输入文档集合一致，RRF 融合时 document.id 才能对上）。
        """
        self.vector_store = vector_store
        self.keyword_search = keyword_search
        self.fusion = fusion
        self.reranker = reranker

    def retrieve(
        self,
        query: str,
        candidate_k: int = 10,
        top_k: int = 5,
    ) -> list[dict]:
        """混合检索：输入用户问题，返回经"召回→融合→精排"后的最终 Top-K。

        参数说明：
            query:       用户问题（纯文本）。
            candidate_k: 召回阶段每路（向量/BM25）各取多少条候选，默认 10。
                         这个数可以比 top_k 大一些——召回求全，宁可多捞一些
                         候选，交给精排去粗取精。
            top_k:       精排后最终返回几条结果（喂给 LLM 的条数），默认 5。

        返回：list[dict]（结构同 reranker.rerank 的输出），每个元素形如
            {
                "document":      Document,  # 命中的文档切片对象
                "score":         float,     # 融合分（RRF 总分，原样保留）
                "rank":          int,       # 精排后的最终名次，从 1 开始
                "rerank_score":  float,     # CrossEncoder 精排分（越大越相关）
            }
            按精排分从高到低排列，共 top_k 条。

        完整流程（四个步骤与下面行内注释一一对应）：
            1. 语义召回：向量检索，取 candidate_k 条；
            2. 关键词召回：BM25 检索，取 candidate_k 条；
            3. RRF 融合：把两路榜单合成一份，取并集按融合分排序；
            4. 精排：CrossEncoder 给融合结果逐条重新打分，取最相关的 top_k 条。
        """

        # ---- 第 1 步：语义召回（Vector Search）----
        # 用向量相似度捞"意思相近"的文档（懂同义改写，可能带进少量噪音）
        vector_results = (
            self.vector_store.search(
                query=query,
                k=candidate_k,
            )
        )

        # ---- 第 2 步：关键词召回（BM25）----
        # 用词面匹配捞"术语/编号精准命中"的文档（不认同义词，但命中即准）
        # 两路召回各取 candidate_k 条，互为补充
        keyword_results = (
            self.keyword_search.search(
                query=query,
                k=candidate_k,
            )
        )

        # ---- 第 3 步：RRF 融合 ----
        # 把两路榜单按"名次"折成分数合榜：
        # 只在一路命中的文档得 1 份分；两路都命中的累加，天然更靠前
        fused_results = (
            self.fusion.fuse(
                [
                    vector_results,
                    keyword_results,
                ]
            )
        )

        # ---- 第 4 步：交叉编码器精排 ----
        # 融合榜只是"粗排"，还存在混合进来的低质结果；
        # Reranker 用更强的模型对每条 (query, 文档) 精细比对，
        # 重新排序后只留最相关的 top_k 条，作为最终答案上下文
        final_results = (
            self.reranker.rerank(
                query=query,
                results=fused_results,
                top_k=top_k,
            )
        )

        # 返回最终精排后的 Top-K 结果
        return final_results
