import os

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from pydantic import SecretStr


load_dotenv()

# =========================
# 1. Embedding Model
# =========================
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


from langchain_community.vectorstores import FAISS

from app.knowledge import documents

from langchain_openai import ChatOpenAI

# =========================
# 2. Chat Model
# =========================
llm = ChatOpenAI(
    model=os.environ["LLM_MODEL"],
    api_key=SecretStr(os.environ["LLM_API_KEY"]),
    base_url=os.environ["LLM_BASE_URL"],
)



# =========================
# 3. 创建 Vector Store
# =========================
vector_store = FAISS.from_documents(
    documents,
    embeddings,
)

# 现在是

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

# 我们的知识库已经建立完成

# =========================
# 4. 创建 Retriever
# =========================
# 创建Retriever
retriever = vector_store.as_retriever(
    # search_type="similarity",
    search_kwargs={"k": 3},
)

# 接受用户信息

# =========================
# 5. 用户问题
# =========================
# query = "Spring Boot 如何连接 MySQL 数据库"

# query = "Redis 是干什么的？"

# query = "RAG是什么？"

query = "公司的年假有多少天？"

# 流程如下
"""  
query
 ↓
retriever

"""

# =========================
# 6. Retrieval
# =========================
results = retriever.invoke(query)

for doc in results:
    print(f"source: {doc.metadata['source']}")
    print(f"category: {doc.metadata['category']}")
    print(f"content: {doc.page_content}")
    print("-" * 50)
    
    
# 运行结果 

"""  
source: mysql.md
category: database
content: Spring Boot 可以通过配置 DataSource 连接 MySQL 数据库。通常需要配置 数据库 URL、用户名和密码。
--------------------------------------------------
source: spring-boot.md
category: java
content: Spring Boot 是一个用于快速开发 Java 应用程序的框架。它通过自动配置和 Starter 简化了 Spring 应用的开发。
--------------------------------------------------
source: redis.md
category: database
content: Redis 是一个基于内存的高性能键值数据库，通常用于缓存、分布式锁、Session 以及其他需要高速访问的数据场景。
--------------------------------------------------

"""

# 到这里我们完成 
""" 
用户问题
    ↓
Retriever
    ↓
相关知识
"""


# 但是现在还不是RAG，目前我们只是实现了检索功能
"""  
Query
 ↓
Retriever
 ↓
Documents

"""
# 也就是说只是 Retriever  还没有Generation

# 下面继续接入LLM


# 目前我们的系统和两个大模型进行交互

""" 
Embedding Model
       │
       └── 用于检索


Chat Model
       │
       └── 用于生成答案

"""

# Retriever找到了
""" 
source: mysql.md
category: database
content: Spring Boot 可以通过配置 DataSource 连接 MySQL 数据库。通常需要配置 数据库 URL、用户名和密码。
--------------------------------------------------
source: spring-boot.md
category: java
content: Spring Boot 是一个用于快速开发 Java 应用程序的框架。它通过自动配置和 Starter 简化了 Spring 应用的开发。
--------------------------------------------------
source: redis.md
category: database
content: Redis 是一个基于内存的高性能键值数据库，通常用于缓存、分布式锁、Session 以及其他需要高速访问的数据场景。
---------------------------------------

"""
# =========================
# 7. 构造 Context
# =========================
# 我们需要将它组合
context = "\n\n".join(
    document.page_content
    for document in results
)

# 现在构造RAG Prompt，这是RAG最核心的一步之一

""" 
我们告诉 LLM：

下面是从知识库中检索出来的资料。

请根据资料回答用户问题。

如果资料中没有答案，
就不要自己编造。
"""

# =========================
# 8. 构造 Prompt
# =========================
prompt = f"""
你是一个企业知识库助手。

请严格根据下面提供的知识回答问题。

如果知识库中没有相关信息，
请明确告诉用户“知识库中没有找到相关信息”，
不要自行编造答案。

知识库内容：
{context}

用户问题：
{query}
"""

# 这里发生的事情如下：

""" 
Retrieved Documents
        +
User Query
        ↓
      Prompt

"""
# 也就是所谓的   Augmented

# 最后将Prompt交给LLM生成答案
# =========================
# 9. LLM Generation
# =========================

results = llm.invoke(prompt)

# =========================
# 10. 输出结果
# =========================
print(results.content)