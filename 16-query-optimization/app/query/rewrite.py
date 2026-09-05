from app.llm.client import chat
from app.query.base import (
    BaseQueryTransformer,
    Query,
    TransformedQuery,
)

REWRITE_SYSTEM_PROMPT = """
你是一名专业的搜索查询优化专家。

你的任务是：
将用户的问题改写成适合知识库检索的搜索查询。

要求：

1. 保留用户原始问题的核心语义。
2. 提取关键技术术语。
3. 补充必要的专业术语。
4. 不要回答用户的问题。
5. 只返回改写后的查询。
6. 不要添加解释。
"""


class QueryRewriter(
    BaseQueryTransformer
):

    def transform(
        self,
        query: Query,
    ) -> list[TransformedQuery]:

        rewritten = chat(
            messages=[
                {
                    "role": "system",
                    "content": (
                        REWRITE_SYSTEM_PROMPT
                    ),
                },
                {
                    "role": "user",
                    "content": query.text,
                },
            ],
            temperature=0.0,
        )

        return [
            TransformedQuery(
                text=rewritten,
                original_query=query.text,
                strategy="rewrite",
            )
        ]
