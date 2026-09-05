from typing import Any


class RAGService:

    def __init__(
        self,
        retriever: Any,
        reranker: Any,
        llm: Any,
    ):
        self.retriever = retriever
        self.reranker = reranker
        self.llm = llm

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:

        documents = self.retriever.search(
            query=query,
            top_k=top_k,
        )

        if self.reranker is not None:
            documents = self.reranker.rerank(
                query=query,
                documents=documents,
                top_k=top_k,
            )

        return documents

    def answer(
        self,
        query: str,
        top_k: int = 5,
    ) -> dict:

        documents = self.retrieve(
            query=query,
            top_k=top_k,
        )

        context = "\n\n".join(
            document["content"]
            for document in documents
        )

        prompt = f"""
                    请根据下面的 Context 回答问题。

                    Context:
                    {context}

                    Question:
                    {query}

                    要求：
                    1. 只能根据 Context 回答。
                    2. 如果 Context 中没有答案，请明确说不知道。
                    """

        answer = self.llm.chat(
            prompt
        )

        return {
            "answer": answer,
            "documents": documents,
        }


# 关系如下：

"""
RAGService
│
├── retrieve()
│     │
│     ├── Retriever
│     └── Reranker
│
└── answer()
      │
      ├── retrieve()
      ├── Context
      ├── Prompt
      └── LLM
"""


# 设计 RAG 的 Evaluation 接口

# 这里是这次课程重点修正的地方。

# Evaluation 不应该自己重新实现 RAG。

# 我们的 RAG 应该提供：

# retrieve()

# 例如：

# class RAGService:

#     def retrieve(
#         self,
#         query: str,
#         top_k: int = 5,
#     ) -> list[dict]:
#         ...

# 它负责：

# Query
#  ↓
# Embedding
#  ↓
# Vector Search
#  ↓
# Reranker
#  ↓
# Top K
#  ↓
# Documents

# 然后 Evaluation 调用：

# RAGEvaluator
#      ↓
# RAGService.retrieve()
#      ↓
# Retrieved Documents
#      ↓
# 计算指标
