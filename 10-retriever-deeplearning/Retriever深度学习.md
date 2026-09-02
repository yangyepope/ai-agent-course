# 一、先建立一个非常重要的认知

很多初学者认为：

Vector Search
    ↓
找到最相似的 Chunk
    ↓
交给 LLM

这就是 RAG。

实际上：

向量相似 ≠ 一定相关。

例如知识库里有：

Chunk A:
Spring Boot 3.4 如何连接 MySQL 8.0

Chunk B:
Spring Boot 3.5 如何连接 MySQL 8.4

Chunk C:
Spring Boot 基础教程

Chunk D:
MySQL 安装教程

用户问：

Spring Boot 3.5 如何连接 MySQL 8.4？

Embedding Search 可能找到：

C
A
B
D

甚至：

A
C
B
D

但真正最有价值的其实是：

B

所以企业 RAG 往往需要：

召回
 ↓
重新排序
 ↓
精选

也就是：

Recall → Rerank

# 二、先理解 Top K

上一课我们使用：

results = vector_store.similarity_search(
    query,
    k=3,
)

这里：

k=3

就是：

找最相关的 3 个 Chunk。

假设搜索结果：

Score

0.92  Chunk A
0.87  Chunk B
0.81  Chunk C
0.76  Chunk D
0.61  Chunk E

那么：

k=3

返回：

A
B
C

这就是：

Top K Retrieval

# 三、为什么不能 K=1？

看一个实际例子。

用户：

Spring Boot 如何连接 MySQL？

可能需要两段知识：

Chunk A:
Spring Boot 数据源配置方式。

Chunk B:
MySQL JDBC URL 配置方式。

如果：

k=1

可能只找到：

Chunk A

LLM：

我知道 Spring Boot 可以配置 DataSource，
但是不知道 MySQL URL 怎么配置。

所以：

K 太小
→ 召回不足

# 四、那为什么不能 K=100？

因为：

Top 100
 ↓
100 个 Chunk
 ↓
全部塞给 LLM

会产生：

Context 太长
Token 消耗增加
噪声增加
无关信息增加
LLM 注意力下降

所以：

K 太小
→ 找不到答案

K 太大
→ 噪声太多

这就是 RAG 中非常经典的：

Recall 与 Precision 的平衡

# 五、Recall 和 Precision

你作为后端开发，可以把它简单理解为：

Recall

相关内容有没有被召回？

例如真实相关 Chunk 有：

A
B
C

你召回：

A
B
D
E

那么：

A
B

找到了。

说明：

Recall 不错
Precision

召回的东西里面，有多少是真正相关的？

例如：

A
B
D
E
F
G

只有：

A
B

真正相关。

那么 Precision 就不高。

# 六、企业 RAG 通常怎么玩？

非常经典的一种架构：

User Query
     │
     ▼
Embedding
     │
     ▼
Vector Search
     │
     ▼
Top 20 / Top 50
     │
     ▼
Reranker
     │
     ▼
Top 3 / Top 5
     │
     ▼
LLM

也就是说：

第一阶段负责“别漏掉”。

第二阶段负责“选准确”。

# 七、这就是 Reranker

Reranker：

Re
+
Rank

就是：

重新给检索结果排序。

例如 Vector Search：

Query:
Spring Boot 3.5 如何连接 MySQL 8.4？

↓ Vector Search

A 0.91
C 0.88
D 0.86
B 0.84

Vector Search 认为：

A
C
D
B

比较相似。

然后 Reranker 重新判断：

Query + Document

可能得到：

B 0.97
A 0.89
C 0.62
D 0.31

最终：

B
A

进入 LLM。

# 八、为什么 Reranker 往往比 Embedding 更“精细”？

Embedding 通常：

Query
 ↓
Vector

然后：

Vector ↔ Vector

比较相似度。

Reranker 则可以直接看：

Query
+
Document

一起判断：

这个 Document
到底是不是回答这个 Query 的？

所以可以把它粗略理解成：

Embedding
→ 快速粗筛

Reranker
→ 精细判断
# 九、一个非常重要的架构

因此企业 RAG 经常是：

                    Query
                      │
                      ▼
                 Query Embedding
                      │
                      ▼
              ┌───────────────┐
              │ Vector Search │
              └───────┬───────┘
                      │
                  Top 20~50
                      │
                      ▼
              ┌───────────────┐
              │   Reranker    │
              └───────┬───────┘
                      │
                   Top 3~10
                      │
                      ▼
                    LLM

这个架构你以后面试的时候一定会遇到。

# 十、现在回到 LangChain

我们先学习 Retriever 的几个重要能力。

1. similarity_search

最基础：

results = vector_store.similarity_search(
    query,
    k=3,
)

意思：

根据向量相似度
找 Top 3

# 十一、similarity_search_with_score

我们还可以获取分数：

results = vector_store.similarity_search_with_score(
    query,
    k=3,
)

然后：

for document, score in results:

    print(
        f"score={score}"
    )

    print(
        document.page_content
    )

注意一个非常重要的问题：

不同 Vector Store 的 score 定义不一定完全相同。

例如 FAISS 某些索引返回的是距离，而不是：

0.0 ~ 1.0

的“相似度”。

所以不要机械地认为：

score 越大
→ 一定越相似

你必须知道当前 Vector Store 使用的距离/评分定义。

# 十二、Similarity Search 的问题

假设：

用户：
Java 后端怎么做缓存？

知识库：

Chunk A:
Java Redis 缓存方案

Chunk B:
Java 本地缓存方案

Chunk C:
Redis 分布式缓存方案

Chunk D:
Java 基础语法

普通 Vector Search：

A
B
C

这三个都和 Query 很相似。

但是：

A
B
C

内容高度重复。

这时候如果：

k=3

我们可能浪费了 3 个结果中的大部分空间。

这就是：

Diversity
# 十三、MMR

LangChain 提供：

MMR

全称：

Maximal Marginal Relevance

你不需要现在记公式。

只需要理解：

既要相关，又要尽量避免内容重复。

普通：

Query
 ↓
Similarity
 ↓
Top K

MMR：

Query
 ↓
相关性
 +
多样性
 ↓
Top K

# 十四、使用 MMR

创建：

retriever = vector_store.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 3,
        "fetch_k": 10,
    },
)

这里：

fetch_k=10

表示：

先找 10 个候选

然后：

k=3

最终：

选 3 个

但是选择的时候不仅考虑：

和 Query 的相关性

还考虑：

彼此之间不要太重复

# 十五、理解 fetch_k

这个概念很重要。

fetch_k

可以理解成：

先召回多少候选？

fetch_k = 20

然后：

MMR
 ↓
从 20 个里面选
 ↓
k = 5

最终：

5 个

所以：

fetch_k
→ 候选池大小

k
→ 最终返回数量
# 十六、Metadata Filter

这是企业 RAG 里面更加重要的东西。

上一课我们给 Document 增加了：

metadata={
    "source": "spring-boot.md",
    "category": "java",
}

假设知识库：

Document A
category = java

Document B
category = database

Document C
category = ai

用户问：

Java 开发规范是什么？

我们可以先过滤：

category = java

然后：

Vector Search

这叫：

Metadata Filtering

# 十七、为什么企业 RAG 特别需要 Metadata Filter？

想象一个 SaaS 系统。

有：

Tenant A
Tenant B
Tenant C

Tenant A 的文档：

tenant_id = A

Tenant B：

tenant_id = B

用户 A 查询：

公司报销制度是什么？

绝对不能搜索到：

Tenant B

的数据。

所以真实企业 RAG：

User Query
    │
    ▼
权限过滤
    │
    ▼
Vector Search
    │
    ▼
Rerank
    │
    ▼
LLM

而不是简单：

User Query
 ↓
Vector Search
 ↓
LLM

# 十八、Metadata 可以存什么？

以后你做企业 RAG，可以设计：

{
    "tenant_id": "company_001",
    "document_id": "doc_123",
    "file_name": "员工手册.pdf",
    "page": 15,
    "department": "finance",
    "category": "policy",
    "created_at": "2026-09-01",
    "permission": [
        "admin",
        "finance"
    ]
}

这样检索的时候就可以：

tenant_id = company_001

以及：

department = finance

再进行：

Vector Search

这就是：

Filter + Vector Search

# 十九、这其实已经开始接近企业级 RAG

现在我们的 Retrieval Pipeline 已经从：

Query
 ↓
Vector Search
 ↓
Top K

升级成：

Query
 ↓
Metadata Filter
 ↓
Vector Search
 ↓
Top N
 ↓
Reranker
 ↓
Top K
 ↓
LLM

再进一步：

Query
 ↓
Query Rewrite
 ↓
Hybrid Search
 ↓
Metadata Filter
 ↓
Vector Search
 ↓
Keyword Search
 ↓
Fusion
 ↓
Reranker
 ↓
Top K
 ↓
LLM

这才是后面我们真正要学习的东西。

# 二十、Query Rewrite 是什么？

假设用户说：

我那个东西怎么弄？

这句话对于搜索系统来说非常差。

如果有对话历史：

用户：
我最近在学 Spring Boot。

用户：
我想连接 MySQL。

用户：
那个东西怎么弄？

真正的 Query 应该理解成：

Spring Boot 如何连接 MySQL？

所以可以：

Chat History
+
Current Query
 ↓
Query Rewrite
 ↓
标准搜索 Query

这也是企业 RAG 很常见的技术。

# 二十一、为什么不能直接把整个聊天记录拿去搜索？

例如：

User:
你好

Assistant:
你好，请问有什么可以帮助你？

User:
我最近在学习 Java。

Assistant:
很好。

User:
Spring Boot 怎么连接 MySQL？

真正搜索应该主要关注：

Spring Boot 怎么连接 MySQL？

而不是：

你好
有什么帮助
Java
...

所以：

Conversation
 ↓
Query Rewrite
 ↓
Search Query

非常重要。

# 二十二、Hybrid Search

现在进入一个企业 RAG 非常重要的概念。

假设用户搜索：

Spring Boot 3.5 + MySQL 8.4

Vector Search 擅长：

语义

Keyword Search 擅长：

精确词

比如：

3.5
8.4
Spring Boot
MySQL

这些版本号、类名、错误码、API 名称：

BM25 / Keyword Search

往往非常有价值。

所以：

Vector Search
+
Keyword Search

就是：

Hybrid Search

# 二十三、Hybrid Search 的完整架构
                       Query
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
        Vector Search          Keyword Search
             │                       │
          Top 50                   Top 50
             │                       │
             └───────────┬───────────┘
                         ▼
                       Fusion
                         │
                         ▼
                      Top 20
                         │
                         ▼
                      Rerank
                         │
                         ▼
                       Top 5
                         │
                         ▼
                        LLM

这就是我们后面要做的：

企业级 Retrieval Pipeline

# 二十四、现在你应该重新理解 Retriever

Retriever 并不是：

retriever.invoke(query)

这么简单。

它背后的思想可以是：

Retriever
│
├── Query Rewrite
│
├── Metadata Filter
│
├── Vector Search
│
├── Keyword Search
│
├── Hybrid Search
│
├── MMR
│
├── Rerank
│
└── Top K

当然实际系统不会所有东西都无脑使用。

而是根据业务选择。

# 二十五、我们现在做一个实验

把第 09 课代码拿过来。

创建：

10-retriever/
├── .env
├── data/
│   └── handbook.pdf
└── app/
    └── main.py

然后：

query = "Spring Boot 如何连接 MySQL？"

分别测试：

实验 A：普通 Search
results = vector_store.similarity_search(
    query,
    k=3,
)
实验 B：MMR
retriever = vector_store.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 3,
        "fetch_k": 10,
    },
)

results = retriever.invoke(
    query
)

然后观察两种结果有什么区别。

# 二十六、再做一个 Score Threshold 实验

实际系统经常会遇到：

用户：
新加坡有哪些好吃的餐厅？

但你的知识库是：

Java 开发规范
Spring Boot
MySQL
Redis
RAG

Vector Search 可能还是会找到：

Java
Redis
Spring Boot

因为：

向量搜索通常总能给你一些“最相似”的东西。

即使：

其实根本不相关。

因此需要：

Similarity Threshold

例如：

score < threshold

就认为：

没有足够相关的知识

然后告诉 LLM：

知识库没有找到相关信息。

这比：

无论如何都塞 3 个 Chunk

更加可靠。

# 二十七、但这里有个坑

Threshold 不能随便写：

threshold = 0.8

然后所有模型、所有数据库都使用。

因为：

Embedding Model
Vector DB
Distance Metric
Index
Normalization

都会影响分数。

所以企业 RAG 中：

Threshold 通常需要通过真实数据集评估出来。

这就引出了下一阶段非常重要的内容：

RAG Evaluation

# 二十八、现在整个 Retrieval 系统已经变成这样
                         User Query
                              │
                              ▼
                       Query Rewrite
                              │
                              ▼
                       Metadata Filter
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
        Vector Search                 Keyword Search
               │                             │
               └──────────────┬──────────────┘
                              ▼
                        Hybrid / Fusion
                              │
                              ▼
                         Candidate Set
                              │
                              ▼
                            MMR
                              │
                              ▼
                          Reranker
                              │
                              ▼
                           Top K
                              │
                              ▼
                            LLM

你不需要今天全部实现。

今天最重要的是建立正确的架构认知。

# 二十九、一个真实企业 RAG 不一定这么复杂

这一点也非常重要。

不是：

Query Rewrite
+
Metadata
+
Vector
+
BM25
+
MMR
+
Reranker
+
...

全部打开才叫企业级。

真正应该是：

业务问题
 ↓
数据特点
 ↓
检索实验
 ↓
选择方案

例如：

简单 FAQ

可能：

Vector Search
 ↓
Top 5
 ↓
LLM

就够了。

技术文档

可能：

Hybrid Search
 ↓
Reranker
 ↓
LLM

更合适。

多租户企业知识库

可能：

Permission Filter
 ↓
Hybrid Search
 ↓
Reranker
 ↓
LLM

# 三十、这一课最重要的一句话

你以后一定会反复遇到：

Retriever 的目标不是“找到相似文本”，而是“找到能够回答用户问题的证据”。

这是两个不同的概念。

相似
≠
相关
≠
能够回答问题

这也是为什么：

Embedding

只是 RAG 检索的开始。

# 三十一、第 10 课知识地图

现在你的 RAG 已经从：

                 RAG
                  │
                  ▼
              Embedding
                  │
                  ▼
              Vector DB
                  │
                  ▼
              Retriever
                  │
                  ▼
                 LLM

逐渐变成：

                      RAG Retrieval
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
            Query Rewrite        Metadata Filter
                 │                     │
                 └──────────┬──────────┘
                            ▼
                    ┌───────────────┐
                    │   Retrieval   │
                    ├───────────────┤
                    │ Vector Search │
                    │ BM25          │
                    │ Hybrid Search │
                    │ MMR           │
                    └───────┬───────┘
                            ▼
                         Reranker
                            │
                            ▼
                          Top K
                            │
                            ▼
                         Context
                            │
                            ▼
                           LLM