"""
本地 Embedding（向量化）服务。

作用：
    把文本转换成向量，供 RAG 检索使用。
    与远程 API（OpenAIEmbeddings 接百炼）不同，这里是本地模型方案：
    免费、离线可用、数据不出本机。

用法：
    service = EmbeddingService()                  # 默认加载 BAAI/bge-small-zh-v1.5
    vecs    = service.embed_documents(texts)      # 文档切片列表 -> 向量（入库阶段用）
    vec     = service.embed_query(query)          # 单个问题   -> 向量（检索阶段用）

依赖：
    sentence-transformers（首次运行会自动从 HuggingFace 下载模型并缓存）。

------------------------------------------------------------
这里的职责非常单纯（单一职责原则）：

    文本
     ↓
    EmbeddingService
     ↓
    Vector

它不负责：
    搜索
    排序
    过滤
    Reranker

这些分别由 vector_store.py（检索）、retriever.py（策略）等文件承担。
------------------------------------------------------------
"""

from sentence_transformers import SentenceTransformer  # 加载/推理句子向量模型


class EmbeddingService:
    """
    本地文本向量化服务，是 RAG 里的 Embedding 环节。

    RAG 检索链路：文本 -> Embedding（本类）-> Vector DB -> Retriever

    为什么用本地模型而不是远程 API？
        - 免费、离线可用、数据不出本机；
        - 缺点：首次运行需联网从 HuggingFace 下载模型（约 100MB）。

    怎么选模型？
        - model_name 传 HuggingFace 上任意 sentence-transformers 兼容的
          模型 ID 即可，默认是智源开源的轻量中文模型 BAAI/bge-small-zh-v1.5。
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-zh-v1.5",
    ):
        """加载本地嵌入模型。

        参数说明：
            model_name: 模型 ID。默认 BAAI/bge-small-zh-v1.5（512 维向量），
                        首次调用会自动从 HuggingFace Hub 下载，
                        缓存到 ~/.cache/huggingface/hub/，之后可离线加载。
        """
        self.model = SentenceTransformer(
            model_name
        )

    def embed_documents(
        self,
        texts: list[str],
    ):
        """批量向量化：把【文档切片列表】转成向量（入库阶段用）。

        文档切片在存入向量库之前，先经过本方法变成向量，
        向量库才存得进去、以后才搜得到。

        归一化说明：
            normalize_embeddings=True 会把向量归一化成长度为 1 的单位向量，
            这样 vector_store 里用"内积"就能等价于"余弦相似度"。
        """
        return self.model.encode(
            texts,
            normalize_embeddings=True,
        )

    def embed_query(
        self,
        query: str,
    ):
        """单个向量化：把【用户的问题】转成向量（检索阶段用）。

        用户提问后，先把它变成向量，再去向量库里和文档向量做相似度比对，
        找出最相关的片段。返回的是单个向量（而非二维列表），
        所以 encode 后取 [0] 拿第一行。
        """
        return self.model.encode(
            [query],
            normalize_embeddings=True,
        )[0]
