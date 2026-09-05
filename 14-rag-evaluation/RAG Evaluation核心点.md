# 设计 RAG 的 Evaluation 接口

这里是这次课程重点修正的地方。

Evaluation 不应该自己重新实现 RAG。

我们的 RAG 应该提供：

retrieve()

例如：
```python
class RAGService:

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:
        ...

它负责：

Query
 ↓
Embedding
 ↓
Vector Search
 ↓
Reranker
 ↓
Top K
 ↓
Documents

然后 Evaluation 调用：

RAGEvaluator
     ↓
RAGService.retrieve()
     ↓
Retrieved Documents
     ↓
计算指标
