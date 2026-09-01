

# 问题-
现在你应该主动发现问题。

我们目前：

documents = [
    ...
]

是人工写死的。

现实中不会这样。

现实：

PDF
Word
Excel
Markdown
HTML
网页
数据库
企业知识库

所以需要：

Document Loader

# 问题二
我们现在一个：

Document

基本就是一段短文本。

真实 PDF 可能：

100 页

所以需要：

Chunking


# 问题三
我们的：

FAISS

程序重启之后怎么办？

重新加载？

生产环境怎么办？

所以需要：

Persistent Vector Database

# 问题四
我们现在只用了：

Vector Search

但是企业搜索通常还需要：

Keyword Search
+
Vector Search

也就是：

Hybrid Search


# 问题五
我们直接把 Top 3 全部塞给 LLM：

Top 3
 ↓
LLM

真实企业系统经常还需要：

Retriever
 ↓
Top 20
 ↓
Reranker
 ↓
Top 5
 ↓
LLM

# 所以企业级 RAG 会逐渐变成这样
                       Knowledge
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
         PDF              Word             Web
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                    Document Loader
                           │
                           ▼
                       Chunking
                           │
                           ▼
                       Embedding
                           │
                           ▼
                  Vector Database
                           │
                           │
                    ┌──────┴──────┐
                    │             │
                 Vector         Keyword
                 Search          Search
                    │             │
                    └──────┬──────┘
                           ▼
                     Hybrid Search
                           │
                           ▼
                        Rerank
                           │
                           ▼
                       Top K Docs
                           │
                           ▼
                  Context + Query
                           │
                           ▼
                          LLM
                           │
                           ▼
                         Answer

# 最后故意问


query = "公司的年假有多少天？"

你会发现最后一个问题可能也会得到一些“看起来合理”的答案。

这正好暴露了 RAG 的一个重大问题：

Hallucination

所以我们的 Prompt 才要求：

如果知识库中没有相关信息，
不要自行编造。

但是仅仅靠 Prompt：

并不能彻底解决幻觉。

后面我们还会学习：

Retrieval Score Threshold
Reranker
Groundedness
Citation
Evaluation

这些才是企业 RAG 真正需要解决的问题。