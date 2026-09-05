from app.config import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
)
from openai import OpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
)

client = OpenAI(
    api_key=LLM_API_KEY.get_secret_value(),
    base_url=LLM_BASE_URL,
)


def chat(
    messages: list[ChatCompletionMessageParam],
    temperature: float = 0.0,
) -> str:

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=temperature,
    )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError(
            "LLM 返回内容为空"
        )

    return content.strip()
