"""
课程 10（Retriever 深度学习）的 RAG 检索演示入口。

作用：
    把本项目的前面几个模块串起来，跑通一次完整的"文档检索"：
        config.py        加载本地文档切片（json 文件 -> Document 列表）
        embeddings.py    本地 Embedding 服务（文本 -> 向量）
        vector_store.py  向量索引与检索（FAISS）
        main.py          （本文件）编排以上流程并打印检索结果

运行方式：
    cd /opt/ai-agent-course/10-retriever-deeplearning
    .venv/bin/python -m app.main

依赖前提：
    - 需要安装 sentence-transformers（首次运行会自动下载 BAAI/bge-small-zh-v1.5）
    - 需要 data/documents.json 文档数据
"""

from app.config import load_documents
from app.embeddings import EmbeddingService
from app.vector_store import VectorStore
from app.retriever import Retriever


def main():
    """跑一次完整检索：加载文档 -> 向量化建库 -> 语义搜索 -> 打印结果。

    整体流程：
        1. load_documents()     从 data/documents.json 读取全部文档切片
        2. EmbeddingService()   初始化本地向量化模型（首次运行自动下载）
        3. VectorStore(...)     把所有文档切片向量化后存入 FAISS 索引
        4. vector_store.search() 把用户问题向量化，检索最相似的 Top-K 文档
        5. 打印每条结果的排名、相似度与文档元信息
    """

    # 1. 加载文档：把 data/documents.json 解析成 Document 对象列表
    #    （每份 Document 包含 id / content / source / page / category 五个字段）
    documents = load_documents()

    # 2. 创建本地 Embedding 服务
    #    默认加载模型 BAAI/bge-small-zh-v1.5；
    #    若 sentence-transformers 未安装，此处会抛 ImportError
    embedding_service = EmbeddingService()

    # 3. 构建向量库
    #    构造 VectorStore 时内部会做两件事：
    #      a. 用 embedding_service 把每份文档的 content 向量化；
    #      b. 把向量加入 FAISS 索引（IndexFlatIP，内积=余弦相似度）。
    vector_store = VectorStore(
        documents=documents,
        embedding_service=embedding_service,
    )
    
    
    retriever = Retriever(vector_store=vector_store)

    # 4. 用户问题（示例：模拟一个员工咨询报销规则的场景）
    query = "出差的时候交通费可以报销吗？"

    # 5. 语义检索：在全部文档里找与 query 最相似的 k=5 条
    #    返回按相似度降序排列的 list[dict]，每条含 document/score/rank
    # results = vector_store.search(
    #     query,
    #     k=3,
    #     # 添加分数阈值，只返回相似度高于 0.6 的结果
    #     # score_threshold=0.6,
    #     category="finance",
    # )
    
    # results = vector_store.mmr_search(
    # query="公司的报销制度是什么？",
    # k=3,
    # fetch_k=6,
    
    # #     lambda_mult

    # # 控制：

    # # 相关性
    # # vs
    # # 多样性

    # # 可以简单理解：

    # # lambda 越大
    # # → 越重视相关性

    # # lambda 越小
    # # → 越重视多样性
    # lambda_mult=0.5, 
    
    
    results = retriever.retrieve(
        query="公司的报销制度是什么？",
        top_k=3,
        search_type="mmr",
        # lambda_mult：相关性 vs 多样性的平衡系数（0~1）
        #   0.9 = 非常重视相关性 -> Redis 这类"不相关但多样"的结果会被压下去
        #   0.5 = 五五开（默认），多样性权重高，容易出现"看似无关"的排位
        lambda_mult=0.9,
        category="finance",
    )
    


    # 6. 打印检索结果：排名、相似度分数，以及命中文档的全部元信息
    for result in results:

        document = result["document"]

        print("=" * 60)

        # rank：命中顺序，1 表示与问题最相似
        print(
            f"Rank: {result['rank']}"
        )

        # score：相似度分数（0~1，越大越相似）
        print(
            f"Score: {result['score']:.4f}"
        )

        # 以下为命中文档的元信息（来自 data/documents.json）
        print(
            f"ID: {document.id}"
        )

        # 文档来源（如手册名/文件名）
        print(
            f"Source: {document.source}"
        )

        # 命中的页码（便于回到原文核对）
        print(
            f"Page: {document.page}"
        )

        # 所属分类（如"差旅报销"）
        print(
            f"Category: {document.category}"
        )

        # 命中的正文切片
        print(
            f"Content: {document.content}"
        )


# 只有直接运行本文件时才执行 main()；
# 被其他模块 import 时不触发，避免副作用
if __name__ == "__main__":
    main()
