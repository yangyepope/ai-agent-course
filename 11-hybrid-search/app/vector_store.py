"""
向量存储与检索服务（基于 FAISS）。

作用：
    1. 构建索引：把所有文档用 EmbeddingService 向量化后，存入 FAISS 索引；
    2. 相似检索：把用户问题向量化，在索引中找出最相似的 Top-K 个文档。

在 RAG 链路中的位置：
    文档切片 -> Embedding(embeddings.py) -> VectorStore(本文件，FAISS) -> Retriever -> LLM
    也就是说：VectorStore 就是课程里讲的 "Vector DB" 的最简落地实现。

技术选型说明：
    - 使用 faiss-cpu 的 IndexFlatIP（内积索引，暴力全量扫描）。
      因为入库时 embed_documents / embed_query 都开了 normalize_embeddings=True
      （向量已归一化），此时"内积"就等于"余弦相似度"。
    - 索引全部存在内存中，进程退出即销毁——适合教学/原型，
      企业级场景会换成持久化的向量库（如 Milvus、pgvector、Elasticsearch）。
"""

import faiss
import numpy as np

from app.embeddings import EmbeddingService
from app.models import Document


class VectorStore:
    """
    一个极简的内存版向量数据库。

    对外暴露两个检索能力：
        - search()：    纯相似度检索，返回最相似的 Top-K 文档（支持过滤）；
        - mmr_search()：最大边际相关检索，在"相关"与"多样"间平衡。

    构造时接收全部文档，自动完成"向量化 + 建索引"。
    """

    def __init__(
        self,
        documents: list[Document],
        embedding_service: EmbeddingService,
    ):
        """初始化：保存文档与 embedding 服务，并立刻构建向量索引。

        参数说明：
            documents:         全部文档切片（每个元素是 Document，content 为纯文本）
            embedding_service: 负责文本 <-> 向量 转换的服务实例
        """
        self.documents = documents
        self.embedding_service = embedding_service

        self._build_index()

    def _build_index(self):
        """把全部文档向量化，构建 FAISS 索引（构造时自动调用一次）。

        步骤：
            1. 取出每个 Document 的 content 纯文本；
            2. 用 embedding_service 批量生成向量（list[list[float]]）；
            3. 转成 FAISS 要求的 float32 二维 numpy 数组；
            4. 根据向量维度创建 IndexFlatIP（内积相似度索引）；
            5. 把所有文档向量 add 进索引。
        """
        # 1. 只取纯文本内容（embedding 模型吃的是字符串，不是 Document 对象）
        texts = [
            document.content
            for document in self.documents
        ]

        # 2. 批量向量化：每段文本 -> 一个向量
        embeddings = (
            self.embedding_service
            .embed_documents(texts)
        )

        # 3. FAISS 只认 float32 的二维 ndarray：形状为 (文档数, 向量维度)
        embeddings = np.asarray(
            embeddings,
            dtype="float32",
        )

        # 4. 向量维度（embedding 模型输出向量的长度，如 bge-small 是 512）
        dimension = embeddings.shape[1]

        # 5. IndexFlatIP = 内积(Inner Product)索引，暴力扫描全部向量求相似度；
        #    因为向量已归一化，内积值即余弦相似度，值越大越相似
        self.index = faiss.IndexFlatIP(
            dimension
        )

        # 6. 把文档向量全部加入索引，之后 search 就能在里面找
        self.index.add(embeddings)

    def _similarity(
        self,
        a: np.ndarray,
        b: np.ndarray,
    ) -> float:
        """计算两个向量的相似度。

        向量在入库时已归一化（normalize_embeddings=True），
        因此内积 np.dot(a, b) 就等于余弦相似度，范围约 [-1, 1]。

        在 MMR 检索中用于计算：
           - relevance：候选文档与 query 的相似度（越大越相关）；
           - diversity：候选文档与已选文档的相似度（越大越重复）。
        """
        return float(
            np.dot(a, b)
        )

    def _reconstruct(
        self,
        index: int,
    ) -> np.ndarray:
        """取回索引中第 index 个文档的原始向量。

        为什么需要这个方法：
           faiss 的类型声明里 reconstruct 单参数调用时返回类型不确定
           （可能被推断为 torch.Tensor 或 ndarray），
           这里显式 asarray 固定为 float32 的 ndarray，
           既让类型检查通过，也保证 _similarity 里 np.dot 拿到的是数组。
        """
        return np.asarray(
            self.index.reconstruct(index),
            dtype="float32",
        )

    def search(
        self,
        query: str,
        k: int = 5,
        score_threshold: float | None = None,
        category: str | None = None,
    ) -> list[dict]:
        """语义检索：输入用户问题，返回最相似的 Top-K 个文档。

        参数说明：
            query:           用户问题（纯文本）
            k:               最多返回几条结果（Top-K）
            score_threshold: 相似度门槛，可传 None 表示不过滤。
                             命中结果的 score 低于该值会被丢弃，
                             例如设为 0.7 就只返回相似度 >= 0.7 的文档，
                             用于过滤掉"看起来像但实际不相关"的噪音结果。
            category:        类别过滤：只返回 category 与该值相同的文档；
                             None 表示不过滤。

        返回结构：list[dict]，每个 dict 形如
            {
                "document": Document,   # 命中的原始文档切片对象
                "score":    float,      # 相似度分数（越大越相似，约 0~1）
                "rank":     int,        # 排名，从 1 开始（过滤后重新编号）
            }
        结果已按相似度从高到低排序。

        检索思想（一个非常关键的变化）：
            以前是直接 `index.search(query, k)` 只查 k 条；但加了
            category / score_threshold 过滤后会出现问题——
            例如 k=3，可前 3 条里只有 1 条符合 category=finance，
            过滤完就只剩 1 条，白白浪费了检索名额。

            所以现在先查【全量】len(self.documents) 条，让过滤发生在
            "排序候选"阶段，而不是"截断"之后，流水线是：

                全部候选
                    ↓
                Metadata Filter（category 类别过滤）
                    ↓
                Threshold（score_threshold 相似度门槛）
                    ↓
                Top K（凑满 k 条为止）

            候选集越大，过滤后才越不容易"空手而归"。这是非常重要的检索思想。
        """
        # 1. 把用户问题转成单个向量
        query_embedding = (
            self.embedding_service
            .embed_query(query)
        )

        # 2. 包成二维数组：FAISS 的 search 需要形状 (查询数, 维度)
        query_embedding = np.asarray(
            [query_embedding],
            dtype="float32",
        )

        # 3. 在索引里找与问题向量最相似的 k 个：
        #    scores  -> 相似度分数，形状 (1, k)
        #    indices -> 命中文档在 self.documents 里的下标，形状 (1, k)
        #    注意：第二个参数不是 k，而是 len(self.documents)（查全量），
        #    原因见上方 docstring 的"检索思想"——先扩大候选集，
        #    过滤后再自然截断成 Top-K
        scores, indices = self.index.search(
            query_embedding,
            len(self.documents),
        )

        # 4. 把 (分数, 下标) 组装成易读的结果列表
        #    注意：FAISS 返回的分数是降序的，因此这里天然按相似度从高到低排列
        results = []

        for score, index in zip(
            scores[0],
            indices[0],
        ):
            # 4.1 FAISS 结果不足 k 个时用 -1 占位，直接跳过
            if index < 0:
                continue

            document = self.documents[index]

            # 4.2 Metadata Filter（类别过滤）：
            #     若指定了 category，且该文档不属于该类别，丢弃
            if (
                category is not None
                and document.category != category
            ):
                continue

            score = float(score)

            # 4.3 Similarity Threshold Filter（相似度门槛过滤）：
            #     若设置了 score_threshold，且当前分数低于门槛，
            #     说明这条结果太"不相关"，丢弃（返回结果会更少但更精）
            if (
                score_threshold is not None
                and score < score_threshold
            ):
                continue

            # 4.4 追加结果；rank 用 len(results) + 1 动态编号，
            #     保证过滤掉低分项后，排名仍然连续从 1 开始
            results.append(
                {
                    "document": document,
                    "score": score,
                    "rank": len(results) + 1,
                }
            )

        return results

    def mmr_search(
        self,
        query: str,
        k: int = 3,
        fetch_k: int = 10,
        lambda_mult: float = 0.5,
    ) -> list[dict]:
        """MMR（最大边际相关）检索：既相关、又不重复的 Top-K。

        为什么需要 MMR：
            纯相似度检索可能把"讲同一件事的 N 个片段"全选上来，
            信息高度重复。MMR 逐个挑选时同时惩罚"与已选结果的重复度"：

                mmr_score = lambda * relevance - (1 - lambda) * diversity

            参数说明：
                query:       用户问题（纯文本）
                k:           最终返回几条结果
                fetch_k:     先取多少条候选（Top-K 的"池塘"，越大越不易漏）
                lambda_mult: 平衡系数，越大越重视"相关"、越小越重视"多样"
                             （0.5 表示两者五五开）
        """
        # 1. 把用户问题转成单个向量，并包成 FAISS 需要的二维数组
        query_embedding = (
            self.embedding_service
            .embed_query(query)
        )

        query_embedding = np.asarray(
            query_embedding,
            dtype="float32",
        )

        # 2. 第一阶段：粗召回——先按相似度取出 fetch_k 个候选
        scores, indices = self.index.search(
            np.asarray(
                [query_embedding],
                dtype="float32",
            ),
            fetch_k,
        )

        # FAISS 返回的 indices 是 numpy 的 int64 数组，
        # 必须转成 Python 原生 int，否则传给 reconstruct() 会报
        # TypeError: argument 2 of type 'faiss::idx_t'
        candidate_indices = [
            int(index)
            for index in indices[0]
            if index >= 0
        ]

        # 3. 第二阶段：MMR 挑选——从候选里逐个选出"既相关又不重复"的，
        #    直到凑满 k 条或候选耗尽
        selected_indices = []

        while (
            candidate_indices
            and len(selected_indices) < k
        ):

            best_index = None
            best_score = float("-inf")

            for candidate_index in candidate_indices:

                document_embedding = self._reconstruct(
                    candidate_index
                )

                # 3.1 relevance：候选文档与问题的相似度（越大越相关）
                relevance = self._similarity(
                    query_embedding,
                    document_embedding,
                )

                # 3.2 diversity：候选文档与【已入选】文档的最大相似度
                #     （越大说明和已选的越重复）
                if not selected_indices:
                    diversity = 0.0
                else:
                    similarities = []

                    for selected_index in selected_indices:

                        selected_embedding = self._reconstruct(
                            selected_index
                        )

                        similarities.append(
                            self._similarity(
                                document_embedding,
                                selected_embedding,
                            )
                        )

                    diversity = max(
                        similarities
                    )

                # 3.3 MMR 核心公式：
                #     lambda 大 -> 重相关（接近纯相似度检索）
                #     lambda 小 -> 重多样（内容更分散，但可能离题）
                mmr_score = (
                    lambda_mult * relevance
                    - (1 - lambda_mult) * diversity
                )

                # 3.4 记录当前轮 MMR 分最高的候选
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_index = candidate_index

            # 理论上 candidate_indices 非空时 best_index 必被赋值，
            # 加个兜底让类型检查与运行时都安全
            if best_index is None:
                break

            # 3.5 选中该候选：加入结果，并从候选池里移除（避免重复入选）
            selected_indices.append(
                best_index
            )

            candidate_indices.remove(
                best_index
            )

        # 4. 组装返回结果：score 用"候选与问题的原始相似度"（非 MMR 分），
        #    rank 按入选顺序从 1 开始编号
        results = []

        for rank, index in enumerate(
            selected_indices,
            start=1,
        ):
            document = self.documents[index]

            results.append(
                {
                    "document": document,
                    "score": self._similarity(
                        query_embedding,
                        self._reconstruct(
                            index
                        ),
                    ),
                    "rank": rank,
                }
            )

        return results
