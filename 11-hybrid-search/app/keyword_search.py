"""
关键词检索服务（BM25 词频统计版）——Hybrid Search 的"关键词"半边。

作用：
    用传统的关键词匹配（BM25 算法）在文档里找与用户问题最相关的 Top-K。
    和 vector_store.py（语义向量检索）走的是完全不同的路子：

        语义检索（vector_store.py）：理解"意思"——"报销"和"差旅费"也能互相匹配；
        关键词检索（本文件）：    按"字面词"统计——只有文本里真的出现这些词才算命中。

为什么 RAG 要"Hybrid（混合）"这两种？
    两者互补：
        - 语义检索擅长"换一种说法也能搜到"，但可能把不相关的也拉进来；
        - 关键词检索对"专业术语、编号、品牌名"（如 GPT-4、A100、maxmemory）
          命中极准，但它不懂同义词。
    实际系统常把两边的分数融合（如加权求和）再排序，取长补短。

本文件用到的两个库：
    - jieba：中文分词器。英文按空格切就行，中文必须分词，
      "上海自来水来自海上" 切成 ["上海", "自来水", "来自", "海上"]，
      不然 BM25 拿整句当"一个词"统计毫无意义。
    - rank_bm25：BM25 算法的实现。BM25 是搜索引擎的经典排序公式，
      核心思想：词在"某篇文档"里出现得多 -> 加分；
               词在"越多文档"里都出现 -> 越常见越不值钱，降权（IDF 惩罚）。

用法：
    ks = KeywordSearch(documents)   # 构造时自动：分词 + 建 BM25 索引
    ks.search("maxmemory 怎么配置", k=3)
"""

import jieba  # 中文分词器：把句子切成一个个词
from rank_bm25 import BM25Okapi  # BM25 算法实现：基于词频统计打分的检索模型

from app.models import Document  # 文档切片数据结构


class KeywordSearch:
    """
    一个极简的 BM25 关键词检索引擎。

    与 VectorStore 的接口保持一致（同样接收 list[Document]、
    同样暴露 search(query, k) -> list[dict]），
    这样上层做 Hybrid 融合时，两边的调用方式完全对称，便于统一处理。
    """

    def __init__(
        self,
        documents: list[Document],
    ):
        """初始化：保存文档，并立刻完成"全库分词 + 构建 BM25 索引"。

        参数说明：
            documents: 全部文档切片（与喂给 VectorStore 的是同一批文档）。
        """
        self.documents = documents

        # 1. 预处理：把每篇文档的正文 content 都切成词列表
        #    BM25 索引不接受原始字符串，只接受"词列表的列表"
        self.tokenized_documents = [
            self._tokenize(document.content)
            for document in documents
        ]

        # 2. 用分词后的语料构建 BM25 索引
        #    内部会统计每个词在每个文档里的词频(TF)、
        #    以及每个词出现在多少篇文档里（用于 IDF 降权）
        self.bm25 = BM25Okapi(
            self.tokenized_documents
        )

    def _tokenize(
        self,
        text: str,
    ) -> list[str]:
        """把一段文本切成词列表（BM25 的最小统计单位是"词"）。

        jieba.cut() 返回一个迭代器，用 list() 转成列表，
        例如 "报销交通费" -> ["报销", "交通费"]。
        """
        return list(
            jieba.cut(text)
        )

    def search(
        self,
        query: str,
        k: int = 10,
    ) -> list[dict]:
        """关键词检索：输入用户问题，返回按 BM25 分数排名的 Top-K 篇文档。

        参数说明：
            query: 用户问题（纯文本）
            k:     最多返回几条结果（Top-K），默认 10

        返回结构：list[dict]（与 VectorStore.search 完全一致）
            {
                "document": Document,  # 命中的原始文档切片对象
                "score":    float,     # BM25 相关度分数（越大越相关，无固定上限）
                "rank":     int,       # 排名，从 1 开始
            }
        """
        # 1. 用户问题也要先分词，才能和文档的词列表做统计比较
        query_tokens = self._tokenize(
            query
        )

        # 2. 给【每一篇】文档算一个 BM25 分数
        #    返回数组，长度 = 文档总数，第 i 个元素 = 第 i 篇文档的得分
        scores = self.bm25.get_scores(
            query_tokens
        )

        # 3. 按分数从高到低给文档下标排序：
        #    range(len(scores)) 是所有文档下标 0,1,2...
        #    key=lambda index: scores[index] 按每篇的分数排序
        #    reverse=True 分数高的排前面
        ranked_indices = sorted(
            range(len(scores)),
            key=lambda index: scores[index],
            reverse=True,
        )

        # 4. 取前 k 名，组装成与 VectorStore.search 相同的结果结构
        results = []

        for rank, index in enumerate(
            ranked_indices[:k],
            start=1,
        ):

            document = self.documents[index]

            results.append(
                {
                    "document": document,
                    "score": float(scores[index]),
                    "rank": rank,
                }
            )

        return results

# 现在 VectorStore 和 KeywordSearch 已经完全独立