# 一、先回顾上一课

第 08 课我们已经完成：

用户问题
   ↓
Retriever
   ↓
相关 Documents
   ↓
Context
   ↓
Prompt
   ↓
LLM
   ↓
Answer

这已经是一个 Mini RAG。

但是我们的知识来源是：

documents = [
    Document(...),
    Document(...),
]

这只是为了学习方便。

现实项目可能是：

knowledge/
├── 公司制度.pdf
├── Java开发规范.pdf
├── SpringBoot开发规范.docx
├── API接口文档.md
├── 产品说明书.pdf
└── FAQ.xlsx

所以真正的 RAG 第一件事情不是：

用户提问

而是：

把企业知识导入系统。

# 二、RAG 的两个阶段

以后你一定要把 RAG 分成两个阶段。

阶段 1：Indexing

知识入库。

             原始知识
                 │
                 ▼
          Document Loader
                 │
                 ▼
             Document
                 │
                 ▼
             Chunking
                 │
                 ▼
             Embedding
                 │
                 ▼
          Vector Database

这是：

离线/异步处理阶段。

阶段 2：Retrieval

用户查询。

             User Query
                 │
                 ▼
             Embedding
                 │
                 ▼
         Vector Search
                 │
                 ▼
              Top K
                 │
                 ▼
              Rerank
                 │
                 ▼
               LLM
                 │
                 ▼
              Answer

这是：

在线查询阶段。

所以：

RAG
│
├── Indexing
│
└── Retrieval

这两个概念以后做企业级 RAG 必须分清。

# 三、为什么不能把整个 PDF 直接 Embedding？

假设：

公司员工手册.pdf

有：

300 页

里面包含：

公司介绍
员工入职
考勤
请假
报销
薪资
福利
离职
...

如果直接：

300页 PDF
    ↓
1个 Embedding

会有什么问题？

用户问：

员工请假需要提前多久申请？

我们只需要：

请假制度相关内容

但整个 PDF 是：

公司介绍
+
考勤
+
请假
+
报销
+
薪资
+
福利
+
离职
...

语义太庞杂。

所以我们需要：

Chunking
# 四、Chunk 到底是什么？

Chunk 就是：

把一个大 Document 切成多个适合检索的小文本片段。

例如：

原始文档

公司员工手册

第一章 公司介绍
......

第二章 考勤制度
......

第三章 请假制度
员工请假需要提前提交申请。
......

第四章 报销制度
......

切成：

Chunk 1
公司介绍......

Chunk 2
考勤制度......

Chunk 3
请假制度......
员工请假需要提前提交申请。

Chunk 4
报销制度......

然后：

Chunk 1 → Embedding → Vector 1
Chunk 2 → Embedding → Vector 2
Chunk 3 → Embedding → Vector 3
Chunk 4 → Embedding → Vector 4

用户问：

请假需要提前多久？

系统就有机会直接找到：

Chunk 3

而不是整个 300 页 PDF。

# 五、Chunk 并不是越小越好

这是今天最重要的知识之一。

比如原文：

Spring Boot 可以通过配置
DataSource 连接 MySQL 数据库。
通常需要配置数据库 URL、
用户名和密码。

如果切得太碎：

Chunk 1:
Spring Boot

Chunk 2:
DataSource

Chunk 3:
连接 MySQL

Chunk 4:
数据库 URL

Chunk 5:
用户名和密码

语义就被破坏了。

用户问：

Spring Boot 怎么连接 MySQL？

可能需要同时找到：

Chunk 1
Chunk 2
Chunk 3
Chunk 4
Chunk 5

检索效果反而变差。

# 六、也不能切得太大

如果一个 Chunk：

5000 tokens

里面包含：

Java
Spring
MySQL
Redis
Kafka
Docker
Kubernetes
...

用户问：

Redis 怎么使用？

这个 Chunk 虽然包含答案，但：

相关信息占比太低

会导致：

检索噪声
+
Context 过大
+
LLM 注意力下降

所以 Chunk 要在：

太小
   ↕
太大

之间找到一个平衡。

# 七、Chunk Size 和 Chunk Overlap

你以后会经常看到：

RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)

这两个参数非常重要。

chunk_size

表示：

一个 Chunk 尽量包含多少文本。

例如：

chunk_size = 1000

可以粗略理解成：

一个 Chunk ≈ 1000 个字符

注意：

不同 Splitter 和参数体系中，单位可能不同，不能机械地把所有 chunk_size 都理解成 token。

chunk_overlap

表示：

相邻 Chunk 之间保留多少重叠内容。

例如：

chunk_size = 1000
chunk_overlap = 200

大致：

Chunk 1
┌────────────────────────────────────┐
│          1000                      │
└────────────────────────────────────┘
                  ▲
                  │
               overlap
                  │
          ┌────────────────────────────────────┐
          │          1000                      │
          └────────────────────────────────────┘

后一个 Chunk 会保留前一个 Chunk 的一部分内容。

# 八、为什么需要 overlap？

考虑这段文本：

Spring Boot 使用 DataSource
连接 MySQL 数据库。

数据库 URL 配置如下：
jdbc:mysql://localhost:3306/demo

如果刚好切在这里：

Chunk 1:
Spring Boot 使用 DataSource
连接 MySQL 数据库。
Chunk 2:
数据库 URL 配置如下：
jdbc:mysql://localhost:3306/demo

问题不大。

但如果切成：

Chunk 1:
Spring Boot 使用 DataSource
Chunk 2:
连接 MySQL 数据库。
数据库 URL 配置如下：

语义就被切开了。

有 overlap：

Chunk 1:
Spring Boot 使用 DataSource
连接 MySQL 数据库。

Chunk 2:
连接 MySQL 数据库。
数据库 URL 配置如下：

这样上下文衔接更自然。