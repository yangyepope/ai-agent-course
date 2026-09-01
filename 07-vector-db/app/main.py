"""向量数据库演示：用 FAISS 构建向量库并检索最相关的文档。

运行前请在 .env 中配置：
    LLM_EMBEDDING_MODEL  嵌入模型名
    LLM_API_KEY          API 密钥
    LLM_BASE_URL         API 地址（阿里云百炼等兼容接口）
"""

import os

from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from pydantic import SecretStr


load_dotenv()


# 统一用 os.environ 显式读取：缺失时立即抛 KeyError（附变量名），
# 避免 None 悄悄传入模型导致难以定位的运行时错误
embeddings = OpenAIEmbeddings(
    model=os.environ["LLM_EMBEDDING_MODEL"],
    api_key=SecretStr(os.environ["LLM_API_KEY"]),
    base_url=os.environ["LLM_BASE_URL"],
    # 非 OpenAI 服务商（阿里云百炼）只接受原始字符串数组，
    # 关闭 token 化检查可绕过 token id 数组不兼容问题
    check_embedding_ctx_length=False,
)


# 把文本包装成 Document：既保留内容，也为后续携带元数据（metadata）留位置
documents = [
    Document(page_content="Java 是一种面向对象的编程语言。"),
    Document(page_content="Spring Boot 可以快速开发 Java Web 应用。"),
    Document(page_content="MySQL 是一种关系型数据库。"),
    Document(page_content="Redis 是一种内存数据库。"),
    Document(page_content="LangChain 可以帮助开发 LLM 应用。"),
    Document(page_content="LangGraph 可以用来构建复杂的 Agent 工作流。"),
    Document(page_content="RAG 可以让 LLM 使用外部知识。"),
]


# 建库：FAISS.from_documents 接收 Document 列表，内部自动对每条
# page_content 调用 embed_documents 生成向量，并建立 FAISS 索引
vector_store = FAISS.from_documents(
    documents=documents,
    embedding=embeddings,
)


query = "Spring Boot 怎么连接数据库？"


# 检索：返回最相关的 k 条 (Document, score)。
# 注意 FAISS 默认使用 L2 距离，score 越小表示越相似
results = vector_store.similarity_search_with_score(
    query,
    k=3,
)


for document, score in results:
    print(
        f"{score:.4f} - {document.page_content}"
    )
    
""" 
                  documents
                      │
                      ▼
                  Embedding
                      │
                      ▼
                   Vectors
                      │
                      ▼
                    FAISS
"""

# 如何利用 Retriever
""" 
现在理解 Retriever

这是 RAG 中又一个非常重要的概念：

Retriever

它的职责非常简单：

根据 Query 找到最相关的 Document。

所以：

Vector Store

和：

Retriever

不是一回事。

可以理解：

Vector Store
    ↓
负责存储和搜索

Retriever
    ↓
负责“检索”

"""


retriever = vector_store.as_retriever(
    search_kwargs={
        "k": 3
    }
)

results = retriever.invoke(
    "Spring Boot 如何开发后端应用？"
)



for document in results:

    print(
        document.page_content
    )
    
    
""" 
不要觉得这是一个神奇 API。

它本质上就是：

Query
 ↓
搜索相关文档
 ↓
Documents

也就是：

Retriever
"""