import json

from app.llm.client import chat
from app.query.base import (
    BaseQueryTransformer,
    Query,
    TransformedQuery,
)

MULTI_QUERY_SYSTEM_PROMPT = """
你是一名专业的搜索查询优化专家。

你的任务是：
针对用户的问题生成多个不同角度的搜索查询。

要求：

1. 保留原始问题的核心意图。
2. 每个查询关注不同的检索角度。
3. 查询应该适合知识库搜索。
4. 不要回答问题。
5. 不要添加无关信息。
6. 返回 JSON 数组。
7. 数组中的每一项都是字符串。

例如：

[
  "Redis key eviction mechanism",
  "Redis maxmemory-policy",
  "Redis memory eviction"
]
"""


class MultiQueryTransformer(
    BaseQueryTransformer
):

    def __init__(
        self,
        query_count: int = 5,
    ):

        if query_count <= 0:
            raise ValueError(
                "query_count 必须大于 0"
            )

        self.query_count = query_count

    def transform(
        self,
        query: Query,
    ) -> list[TransformedQuery]:

        user_prompt = f"""
用户问题：

{query.text}

请生成 {self.query_count} 个
不同角度的搜索查询。
"""

        response = chat(
            messages=[
                {
                    "role": "system",
                    "content": (
                        MULTI_QUERY_SYSTEM_PROMPT
                    ),
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            temperature=0.3,
        )

        queries = self._parse_response(
            response
        )

        return [
            TransformedQuery(
                text=item,
                original_query=query.text,
                strategy="multi_query",
                metadata={
                    "query_index": index,
                },
            )
            for index, item in enumerate(
                queries
            )
        ]

    def _parse_response(
        self,
        response: str,
    ) -> list[str]:

        try:

            data = json.loads(
                response
            )

        except json.JSONDecodeError:

            return [
                line.strip()
                for line in response.splitlines()
                if line.strip()
            ]

        if not isinstance(
            data,
            list,
        ):
            raise ValueError(
                "Multi Query 返回结果不是数组"
            )

        queries = []

        for item in data:

            if not isinstance(
                item,
                str,
            ):
                continue

            item = item.strip()

            if item:
                queries.append(item)

        if not queries:
            raise ValueError(
                "没有解析出有效 Query"
            )

        return queries
