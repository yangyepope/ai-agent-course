from langchain_core.documents import Document
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)
from dotenv import load_dotenv


document = Document(
    page_content="""
    Spring Boot 是一个用于快速开发 Java
    应用程序的框架。

    Spring Boot 可以通过自动配置和
    Starter 简化 Spring 应用的开发。

    Spring Boot 可以通过配置 DataSource
    连接 MySQL 数据库。

    Redis 是一个高性能的内存数据库，
    常用于缓存和分布式锁。
    """
)


load_dotenv()


splitter = RecursiveCharacterTextSplitter(
    chunk_size=100,
    chunk_overlap=20,
)

chunks = splitter.split_documents(
    [document]
)

for index, chunk in enumerate(
    chunks,
    start=1,
):
    print(f"===== Chunk {index} =====")
    print(chunk.page_content)
    
# 为什么推荐RecursiveCharacterTextSplitter 

""" 
因为它不是简单地：

每 1000 个字符暴力切一刀

它会尝试按照不同的分隔符进行递归切分。

大致思路：

段落
 ↓
换行
 ↓
句子
 ↓
空格
 ↓
字符

也就是：

尽量保持语义完整

因此对于一般 Markdown / TXT / 普通文本，是非常适合入门的。
"""


# 先安装依赖 

""" 
pip install -U pypdf
"""


from langchain_community.document_loaders import (
    PyPDFLoader,
)

# =========================
# 1. 加载 PDF
# =========================

loader = PyPDFLoader(
    "data/handbook.pdf"
)

documents = loader.load()
print(
    f"文档页数：{len(documents)}"
) 

# 这里有个非常重要的概念

"""  
PDF 加载之后：

documents

不是：

list[str]

而是：

list[Document]

每个 Document 类似：

Document
├── page_content
└── metadata


Document(
    page_content="Spring Boot......",
    metadata={
        "source": "handbook.pdf",
        "page": 12,
    }
)


这里的：

page_content

是正文。

而：

metadata

是元数据。

"""

# Metadata 为什么非常重要

"""  
假设用户问：

公司报销标准是什么？

我们检索到：

Chunk

但是最终回答最好能告诉用户：

来源：公司财务制度.pdf
第 15 页

这时候：

metadata

就非常重要。

例如：

print(document.metadata)

可能看到：

{
    "source": "data/handbook.pdf",
    "page": 15
}

所以企业 RAG 中经常保存：

document_id
file_name
page
section
tenant_id
user_id
department
created_at
permission
"""

# 现在将两部分组合起来

from langchain_community.document_loaders import (
    PyPDFLoader,
)

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)


loader = PyPDFLoader(
    "data/handbook.pdf"
)

documents = loader.load()


# =========================
# 2. 创建 Text Splitter
# =========================
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)


# =========================
# 3. Chunking
# =========================
chunks = splitter.split_documents(
    documents
)


print(
    f"原始 Document 数量：{len(documents)}"
)

print(
    f"Chunk 数量：{len(chunks)}"
)

# 现在是
""" 
PDF
 ↓
PyPDFLoader
 ↓
Documents
 ↓
RecursiveCharacterTextSplitter
 ↓
Chunks
"""

# 看看chunk里面有什么

for index, chunk in enumerate(
    chunks[:5],
    start=1,
):

    print(
        f"===== Chunk {index} ====="
    )

    print(
        chunk.page_content
    )

    print(
        chunk.metadata
    )
    
# 这里出现了一个非常重要的RAG数据模型
""" 
以后你可以把一个 Chunk 理解成：

Chunk
│
├── content
│
├── metadata
│
└── embedding

例如：

{
    "content": "Spring Boot 可以配置 DataSource 连接 MySQL。",
    "metadata": {
        "file_name": "spring.pdf",
        "page": 12,
        "category": "java"
    },
    "embedding": [0.12, -0.23, 0.71]
}

这实际上已经非常接近企业 RAG 的数据模型了。
"""
    
# 现在将Chunks放进FAISS

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import os
from pydantic import SecretStr

# =========================
# 4. Embedding Model
# =========================
embeddings = OpenAIEmbeddings(
    model=os.environ["LLM_EMBEDDING_MODEL"],
    api_key=SecretStr(os.environ["LLM_API_KEY"]),
    base_url=os.environ["LLM_BASE_URL"],
    # 非 OpenAI 服务商（阿里云百炼）只接受原始字符串数组，
    # 关闭 token 化检查可绕过 token id 数组不兼容问题
    check_embedding_ctx_length=False,
    # 阿里云百炼 embedding 接口单次最多接受 20 条文本，
    # 设置 chunk_size 让 SDK 内部自动分批提交
    chunk_size=20,
)

# =========================
# 5. 创建 Vector Store
# =========================
vector_store = FAISS.from_documents(
    chunks,
    embeddings,
)

# 现在完整链路变成

"""  
PDF
 ↓
PyPDFLoader
 ↓
Document
 ↓
Chunking
 ↓
Chunk
 ↓
Embedding
 ↓
Vector
 ↓
FAISS
"""

# =========================
# 6. 测试检索
# =========================
query = "AI原生到底是什么？"
results = vector_store.similarity_search(
    query,
    k=3,
)

# =========================
# 7. 输出结果
# =========================

for index, document in enumerate(
    results,
    start=1,
):

    print(
        f"\n===== Result {index} ====="
    )

    print(
        document.page_content
    )

    print(
        "Metadata:",
        document.metadata,
    )
    
# 现在已经已经实现了一条真正的 RAG Indexing Pipeline

"""  
                handbook.pdf
                     │
                     ▼
                PyPDFLoader
                     │
                     ▼
                 Documents
                     │
                     ▼
                 Chunking
                     │
                     ▼
                   Chunks
                     │
                     ▼
                 Embedding
                     │
                     ▼
              Vector Database
"""

# 查询
""" 
用户问题
   │
   ▼
Retriever
   │
   ▼
相关 Chunk
"""

# 再接上一课
"""  
相关 Chunk
    +
用户 Query
    ↓
Prompt
    ↓
LLM
    ↓
Answer
"""



