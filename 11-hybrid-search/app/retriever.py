"""
检索器（Retriever）：统一封装"如何从向量库中取回最相关的文档"。

作用：
    向量库（VectorStore）本身已经会检索（search / mmr_search），
    但调用方（比如未来的 main / 问答链路）不该关心"用哪种检索策略"，
    本文件把"策略选择"收敛成一个入口 retrieve()，对外只暴露一个方法。

在 RAG 链路中的位置：
    文档切片 -> Embedding(embeddings.py) -> VectorStore(FAISS 向量库)
                                              -> Retriever（本文件） -> LLM
    即：Retriever 夹在"向量库"和"大模型"中间，
        负责把用户问题变成"一小段最相关的文档切片"喂给 LLM 当上下文。

支持的两种检索策略：
    1. similarity（默认）：纯相似度检索——只按"和问题的相关程度"排序取 Top-K；
    2. mmr：最大边际相关检索——在"相关"和"多样"之间做平衡，
            避免 Top-K 全是内容几乎一样的重复片段。
    策略名不合法时抛 ValueError，防止拼错字符串悄悄走错分支。
"""

# 只 import 类型用于标注，retrieve() 里实际靠 vector_store 干活，
# 这样本文件不依赖具体向量库实现（FAISS / Milvus 等都能替换进来）
from app.vector_store import VectorStore


class Retriever:
    """
    一个"薄封装"的检索器。

    它自己不存向量、不建索引，只是持有 VectorStore 实例，
    把"选哪种检索策略 + 传哪些参数"的逻辑收拢到 retrieve() 一个方法里。
    好处：上层代码不需要知道 similarity / MMR 的区别，
    想切换策略时只改一个字符串即可。
    """

    def __init__(
        self,
        vector_store: VectorStore,
    ):
        """初始化：注入一个已构建好的向量库。

        参数说明：
            vector_store: VectorStore 实例（内部已完成文档向量化 + FAISS 索引构建）。
        """
        self.vector_store = vector_store

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        search_type: str = "similarity",
        score_threshold: float | None = None,
        category: str | None = None,
        lambda_mult: float = 0.8,
    ) -> list[dict]:
        """检索：输入用户问题，返回最相关的 Top-K 条文档。

        参数说明：
            query:           用户问题（纯文本）。
            top_k:           最多返回几条结果。
            search_type:     检索策略，二选一：
                             - "similarity"：纯相似度检索（默认）；
                             - "mmr"：最大边际相关检索（相关 + 多样）。
            score_threshold: 相似度门槛（仅 similarity 策略生效）：
                             分数低于该值的命中会被丢弃，None 表示不过滤。
            category:        类别过滤（仅 similarity 策略生效）：
                             只返回该类别下的文档，None 表示不过滤。
            lambda_mult:     相关性/多样性平衡系数（仅 mmr 策略生效）：
                             取值 0~1，越大越重视"相关性"、
                             越小越重视"多样性"，默认 0.5。
                             例如想更贴近用户需求（少跑题）可调到 0.8~0.9。

        返回：list[dict]，每个 dict 形如
            {
                "document": Document,  # 命中的文档切片对象（含 content / source / page / category）
                "score":    float,     # 相似度分数（越大越相关）
                "rank":     int,       # 排名，从 1 开始
            }
            结果按相似度从高到低排列。

        为什么把策略拆成两个分支而不是一个方法：
            similarity 和 MMR 的目标不同——
            similarity 要"最像问题的片段"，MMR 还要"片段之间别太重复"，
            两者对候选集的取法、过滤逻辑都不一样，
            所以各自转调 VectorStore 里对应的方法，代码各管各的更清晰。
        """

        # ---- 策略一：纯相似度检索 ----
        # 直接转调 vector_store.search：按相似度降序取 Top-K，
        # 并把 score_threshold（相似度门槛）和 category（类别过滤）原样透传，
        # 过滤掉"看起来像但实际不相关 / 别的类别"的噪音结果
        if search_type == "similarity":

            return self.vector_store.search(
                query=query,
                k=top_k,
                score_threshold=score_threshold,
                category=category,
            )

        # ---- 策略二：MMR（最大边际相关）检索 ----
        # 先取一个更大的候选集 fetch_k（至少 10 条），再在里面挑选：
        # 每条候选同时看"与问题的相关度"和"与已选结果的重复度"，
        # 挑出既相关又不重复的，直到凑满 top_k 条
        if search_type == "mmr":

            return self.vector_store.mmr_search(
                query=query,
                k=top_k,
                fetch_k=max(top_k * 3, 10),
                lambda_mult=lambda_mult,
            )

        # ---- 兜底：不认识的策略名直接报错 ----
        # 不静默返回空列表，否则上层会误以为"没搜到结果"
        # 而实际是传错了 search_type，这种错误要尽早暴露
        raise ValueError(
            f"Unsupported search_type: "
            f"{search_type}"
        )
