"""
本地 Embedding（向量化）服务。

作用：
    把文本转换成向量，供 RAG 检索使用。
    与 main.py 使用的 OpenAIEmbeddings（远程 API，付费）不同，
    这里是本地模型方案：免费、离线、数据不出本机。

用法：
    service = EmbeddingService()                       # 默认加载 BAAI/bge-small-zh-v1.5
    vecs    = service.embed_documents(texts)           # 文档切片列表 -> 向量（入库）
    vec     = service.embed_query(query)               # 单个问题      -> 向量（检索）

依赖：
    sentence-transformers（首次运行会自动从 HuggingFace 下载模型）。
    未安装时 SentenceTransformer 为 None，实例化会抛出 ImportError。
"""


try:
    from sentence_transformers import SentenceTransformer  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - dependency is optional at import time
    # 依赖没装时降级为 None，不阻塞文件导入；
    # 真正使用时（__init__ 里）再抛出明确错误提示安装。
    SentenceTransformer = None  # type: ignore[assignment]


class EmbeddingService:
    """
    本地文本向量化服务，是 RAG 里的 Embedding 环节。

    RAG 检索链路：文本 -> Embedding（本类）-> Vector DB -> Retriever

    为什么用本地模型而不是 OpenAI API？
        - 免费、离线可用、数据不出本机；
        - 缺点是需要安装 sentence-transformers（含 PyTorch），
          首次运行还要联网从 HuggingFace 下载模型。

    怎么选模型？
        - model_name 传 HuggingFace 上任意 sentence-transformers 兼容的
          模型 ID 即可，默认是智源开源中文模型 BAAI/bge-small-zh-v1.5。
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-zh-v1.5",
    ):
        """加载本地嵌入模型。

        首次调用会自动从 HuggingFace Hub 下载 model_name 对应的模型
        （约 100MB），缓存到 ~/.cache/huggingface/hub/，之后离线加载。
        """
        if SentenceTransformer is None:
            raise ImportError(
                "sentence-transformers is not installed. "
                "Please install it with `pip install sentence-transformers`."
            )
        self.model = SentenceTransformer(
            model_name
        )

    def embed_documents(
        self,
        texts: list[str],
    ):
        """批量向量化：把【文档切片列表】转成向量。

        用于入库阶段——文档切片在存入向量数据库前，
        先经过本方法变成向量，向量库才存得进去、以后才搜得到。
        """
        return self.model.encode(
            texts,
            normalize_embeddings=True,
        )

    def embed_query(
        self,
        query: str,
    ):
        """单个向量化：把【用户的问题】转成向量。

        用于检索阶段——用户提问后，先把它变成向量，
        再去向量库里和文档向量做相似度比对，找出最相关的片段。
        """
        return self.model.encode(
            [query],
            normalize_embeddings=True,
        )[0]
        
# 这里将 EmbeddingService 封装成一个单例，避免每次调用都重复加载模型。

""" 
Document
   ↓
Embedding Model
   ↓
Vector
"""
