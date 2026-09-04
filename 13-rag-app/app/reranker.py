"""
该文件的作用如下：


Retriever

主要负责：

从大量文档中快速找候选

例如：

100000 documents
       ↓
Retriever
       ↓
100 documents

而：

Reranker

负责：

100 documents
       ↓
Reranker
       ↓
5 documents

所以：

Retriever = 召回

Reranker = 精排


"""

import re
import time

from app.logging_config import get_logger

logger = get_logger(__name__)


def tokenize(text: str) -> set[str]:
    """
    把文本切成用于比对的 token 集合。

    为什么不能直接 text.split()：
        中文不用空格分词。"Redis内存满了怎么淘汰".split()
        只会得到一个整串，跟任何文档都对不上，
        精排分全是 0，排序等于没做。

    这里的做法：
        1. 英文/数字：按非字母数字切成词（redis、maxmemory、policy）
        2. 中文：切成相邻两字的组合（内存、存满、满了…）

    用二元组（bigram）而不是单字，是因为单字太容易误命中
    —— "保存数据" 里的 "存" 会让它和 "内存" 沾上关系。
    """

    text = text.lower()

    # 英文、数字
    words = set(re.findall(r"[a-z0-9]+", text))

    # 中文字符（连续的汉字段）
    tokens = set(words)

    for run in re.findall(
        r"[\u4e00-\u9fff]+",
        text,
    ):
        if len(run) == 1:
            tokens.add(run)
            continue

        for i in range(len(run) - 1):
            tokens.add(run[i : i + 2])

    return tokens


class SimpleReranker:
    def rerank(
        self,
        query: str,
        documents: list[dict],
        top_k: int,
    ) -> list[dict]:
        """
        输入：Retriever 召回的 hits（ES 原样返回）
        输出：同构的 hits，但每条多一个 _rerank_score，
              并按它从高到低排序、截断到 top_k 条。

        _score（ES 的 RRF 融合分）原样保留，
        这样能对比精排前后的名次变化。
        """

        started = time.perf_counter()

        query_tokens = tokenize(query)

        scored_documents = []

        for document in documents:
            content = document["_source"]["content"]

            document_tokens = tokenize(content)

            # 覆盖率：query 的 token 有多少被这篇文档命中
            # 除以 query 的 token 数，得到 0~1 的分，
            # 比裸命中数好读，也不会因为文档长就占便宜
            if query_tokens:
                score = len(query_tokens & document_tokens) / len(query_tokens)
            else:
                score = 0.0

            scored_documents.append(
                {
                    **document,
                    "_rerank_score": score,
                }
            )

        scored_documents.sort(
            key=lambda item: item["_rerank_score"],
            reverse=True,
        )

        result = scored_documents[:top_k]

        elapsed_ms = (time.perf_counter() - started) * 1000

        logger.info(
            "精排 %d → %d 条 | %.0fms | 最高分 %.3f",
            len(documents),
            len(result),
            elapsed_ms,
            result[0]["_rerank_score"] if result else 0.0,
        )

        # 全部命中率为 0，说明 query 和候选文档一个 token 都没对上。
        # 这种情况下精排等于没做，拼出来的 Context 大概也答不了。
        if result and result[0]["_rerank_score"] == 0.0:
            logger.warning(
                "精排分全为 0，候选与 query 无重叠：query=%r",
                query,
            )

        return result
