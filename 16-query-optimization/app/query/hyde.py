from app.llm.client import chat
from app.query.base import (
    BaseQueryTransformer,
    Query,
    TransformedQuery,
)

HYDE_SYSTEM_PROMPT = """
你是一名知识库检索辅助模型。

请根据用户的问题，
生成一段假设性的专业文档。

要求：

1. 不需要告诉用户答案。
2. 生成类似知识库文档的内容。
3. 使用专业术语。
4. 尽可能覆盖用户问题相关的核心概念。
5. 内容应该适合作为向量检索的语义表示。
6. 不要添加标题。
7. 不要解释你的生成过程。
"""


class HyDETransformer(
    BaseQueryTransformer
):

    def transform(
        self,
        query: Query,
    ) -> list[TransformedQuery]:

        hypothetical_document = chat(
            messages=[
                {
                    "role": "system",
                    "content": (
                        HYDE_SYSTEM_PROMPT
                    ),
                },
                {
                    "role": "user",
                    "content": query.text,
                },
            ],
            temperature=0.3,
        )

        return [
            TransformedQuery(
                text=hypothetical_document,
                original_query=query.text,
                strategy="hyde",
            )
        ]
