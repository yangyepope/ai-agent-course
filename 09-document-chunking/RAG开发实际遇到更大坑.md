# 一 但是这里还有一个非常大的坑
你现在可能觉得：

chunk_size=1000
chunk_overlap=200

是不是以后所有项目都这么写？

不是。

这是一个非常重要的误区。

Chunk 参数没有万能答案。

例如：

API 文档

可能更适合：

按照接口
按照 Endpoint
按照 Markdown Header
法律合同

可能更适合：

按照条款
按照章节
技术文档

可能更适合：

标题
章节
代码块
段落
FAQ

可能直接：

一问一答

所以：

Chunking 本质上是一个数据预处理 / 信息检索问题，而不是简单调两个参数。

# 二、还有一个更严重的问题：PDF 不一定是文本 PDF

例如：

普通 PDF

里面是真的文本：

Spring Boot 是......

那么：

PyPDFLoader

可以直接提取。

但是扫描件：

PDF
└── 图片

里面没有真正的文本。

这时候：

PyPDFLoader
 ↓
几乎没有文本

就会出问题。

需要：

OCR

例如：

PDF
 ↓
OCR
 ↓
Text
 ↓
Chunk
 ↓
Embedding

这也是企业 RAG 里面非常常见的真实问题。

# 三、再进一步：表格怎么办？

例如 PDF 中：

商品	价格	库存
A	100	20
B	200	5

如果简单 PDF Text Extraction：

商品 价格 库存
A 100 20
B 200 5

有时候关系会丢失。

所以企业 RAG 的 Document Parsing 实际上经常比：

PyPDFLoader

复杂得多。

你以后会看到：

Unstructured
Docling
MinerU
PaddleOCR
LlamaParse

等方案。

但现在不要急着全部学。

我们先把 RAG 基础链路打牢。