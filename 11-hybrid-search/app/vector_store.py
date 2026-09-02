"""
向量存储与检索服务（基于 FAISS）。

作用：
    1. 构建索引：把所有文档用 EmbeddingService 向量化后，存入 FAISS 索引；
    2. 相似检索：把用户问题向量化，在索引中找出最相似的 Top-K 个文档。

在 RAG 链路中的位置：
    文档切片 -> Embedding(embeddings.py) -> VectorStore(本文件，FAISS)
    -> Retriever -> LLM
    也就是说：VectorStore 就是课程里讲的 "Vector DB" 的最简落地实现。

技术选型说明：
    - 使用 faiss-cpu 的 IndexFlatIP（内积索引，暴力全量扫描）。
      因为入库时 embed_documents / embed_query 都开了 normalize_embeddings=True
      （向量已归一化），此时"内积"就等于"余弦相似度"。
    - 索引全部存在内存中，进程退出即销毁——适合教学/原型，
      企业级场景会换成持久化的向量库（如 Milvus、pgvector、Elasticsearch）。
"""

import faiss  # FAISS：向量相似度检索库（IndexFlatIP 内积索引）
import numpy as np  # numpy：把 Python 列表转成 FAISS 要求的 float32 数组

from app.embeddings import EmbeddingService  # 本地向量化服务（文本 <-> 向量）
from app.models import Document  # 文档切片数据结构（id/content/source/page/category）


class VectorStore:
    """
    一个极简的内存版向量数据库。

    对外暴露两个能力：
        - 构造时：接收全部文档，自动完成"向量化 + 建索引"；
        - search()：接收用户问题，返回最相似的 Top-K 文档及相似度分数。
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

        # 构造时立即建好索引，之后 search 才能直接查
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

        # 2. 批量向量化：每段文本 -> 一个向量（文档数 个向量）
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

    def search(
        self,
        query: str,
        k: int = 10,
    ) -> list[dict]:
        """语义检索：输入用户问题，返回最相似的 Top-K 个文档。

        参数说明：
            query: 用户问题（纯文本）
            k:     最多返回几条结果（Top-K），默认 10

        返回结构：list[dict]，每个 dict 形如
            {
                "document": Document,  # 命中的原始文档切片对象
                "score":    float,     # 相似度分数（越大越相似，约 0~1）
                "rank":     int,       # 排名，从 1 开始
            }
        结果按相似度从高到低排列（FAISS 返回的分数天然降序）。
        """
        # 1. 把用户问题转成单个向量（embed_query 返回一维向量）
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
        scores, indices = self.index.search(
            query_embedding,
            k,
        )

        # 4. 把 (分数, 下标) 组装成易读的结果列表
        #    enumerate(..., start=1) 直接生成从 1 开始的 rank
        results = []

        for rank, (score, index) in enumerate(
            zip(
                scores[0],
                indices[0],
            ),
            start=1,
        ):

            # 4.1 FAISS 结果不足 k 个时用 -1 占位，直接跳过
            if index < 0:
                continue

            # 4.2 按下标取回对应的原始文档切片
            document = self.documents[index]

            # 4.3 组装成易读结构：文档 + 相似度分数 + 排名
            results.append(
                {
                    "document": document,
                    "score": float(score),
                    "rank": rank,
                }
            )

        return results
