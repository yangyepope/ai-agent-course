"""
定义模型（数据类）。

本文件是整个项目的数据"地基"：
    所有模块之间传递的"一份文档切片"，都是一个 Document 对象。

它做的事情非常简单——用 @dataclass 声明一个结构体：
    只描述"一份文档切片长什么样（有哪些字段）"，
    不含任何业务逻辑，纯粹是一个装数据的容器。

为什么单独放一个文件？
    Document 被 config.py（读 json 造数据）和 vector_store.py（建索引、检索）
    等多处 import，单独定义一份，避免各文件各写各的字段、
    将来字段一变要改好几个地方。

典型使用链路：
    data/documents.json  ->  config.load_documents()   ->  list[Document]
                                                           ↓
                                            vector_store.VectorStore(documents)
                                                           ↓
                                          检索结果里的 result["document"]
"""

from dataclasses import dataclass


@dataclass
class Document:
    """一份文档切片（RAG 中"切分后的最小检索单元"）。

    对应 data/documents.json 里的一条记录：
        一份 PDF / 手册被按页（或按段落）切开后，每一片就是一个 Document。

    字段说明：
        id:       唯一标识，如 "doc-001"（人工编号，用于追踪是哪一条）
        content:  切片正文（纯文本）——向量化、检索比对用的就是它
        source:   文档来源（原文件名，如 finance-policy.pdf），用于回溯原文
        page:     该切片来自原文档的第几页，方便人工核对
        category: 业务分类（如 finance / hr / technical），
                  可用于检索时做类别过滤（category="finance" 只查财务类）

    使用示例（手动构造一个，供测试或造数据用）：
        >>> doc = Document(
        ...     id="doc-001",
        ...     content="员工因公出差的交通费用可按制度报销。",
        ...     source="finance-policy.pdf",
        ...     page=8,
        ...     category="finance",
        ... )
        >>> doc.content      # 取字段
        >>> doc.id, doc.page

    生产环境里一般不自建，而是由 config.load_documents() 读取
    data/documents.json 自动批量生成：
        >>> from app.config import load_documents
        >>> docs: list[Document] = load_documents()

    因为 @dataclass 的功劳，Document 还自带：
        - repr()：打印出来就是清晰的字段列表，方便调试
        - 相等比较：两个 Document 字段全相同即相等
    """

    id: str
    content: str
    source: str
    page: int
    category: str
