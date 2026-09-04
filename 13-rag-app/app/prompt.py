from openai.types.chat import (
    ChatCompletionMessageParam,
)

SYSTEM_PROMPT = """
你是一名专业的企业知识库问答助手。

你的任务是根据提供的知识库内容回答用户问题。

请严格遵守以下规则：

1. 只能根据 Context 中提供的信息回答。
2. 如果 Context 中没有答案，请明确告诉用户“知识库中没有找到相关信息”。
3. 不允许根据自己的知识编造答案。
4. 回答应该准确、清晰、简洁。
5. 如果使用了知识库内容，请说明对应来源。
"""


def build_messages(
    query: str,
    context: str,
) -> list[ChatCompletionMessageParam]:

    user_prompt = f"""
请根据下面的知识库内容回答用户的问题。

====================
Context
====================

{context}

====================
Question
====================

{query}

====================
Answer
====================

请根据 Context 直接回答问题。
"""

    return [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ]
