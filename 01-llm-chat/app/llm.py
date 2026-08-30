"""LLM 聊天核心模块。

本模块封装了与 LLM 服务的交互逻辑，包括：
- 系统提示词（SYSTEM_PROMPT）定义
- 客户端初始化
- 基于会话的多轮对话历史管理
- 与模型进行单轮问答的核心函数 chat()
"""

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from app.config import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
)


# 系统提示词：设定 LLM 的角色、专长与回答风格。
# 它会在每次对话的最前面作为 system 消息发送给模型，
# 用于约束模型的回答行为。
SYSTEM_PROMPT = """
你是一名资深 Java 后端工程师。
你擅长 Spring Boot、MySQL、Redis、Elasticsearch 和 Docker。
回答问题时要尽量给出实际代码示例。
注意：无论用户问什么，你都只以「Java 后端工程师」的身份回答，不要提及你是通义千问或任何大语言模型。
"""


# 每个会话最多保留的历史消息条数。
# 当历史消息超过该数量时，会自动裁剪掉最早的消息，
# 避免上下文无限增长导致 token 消耗过大或超出模型上下文限制。
MAX_HISTORY_MESSAGES = 20


# OpenAI 客户端实例。
# 通过 api_key 与 base_url 连接到指定的 LLM 服务，
# 所有模型调用均通过该客户端完成。
client = OpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL,
)


# 会话历史存储。
# 类型为 dict[str, list[ChatCompletionMessageParam]]，其中：
# - str：字典的 key 类型，即会话 ID（session_id），用于区分不同对话上下文；
# - ChatCompletionMessageParam：字典 value（消息列表）中每条消息的类型，
#   它来自 openai.types.chat，是一个类型别名（Union），
#   代表合法的聊天消息结构（如 {"role": "system", "content": ...}、
#   {"role": "user", ...}、{"role": "assistant", ...} 等），
#   仅用于类型标注/静态检查，不参与运行时逻辑。
# 用于在不同请求之间保持多轮对话的上下文。
chat_history: dict[str, list[ChatCompletionMessageParam]] = {}


def chat(session_id: str, message: str) -> str:
    """处理一次用户消息并返回模型回答。

    该函数会：
    1. 获取（或初始化）指定会话的历史消息列表；
    2. 将系统提示词、历史消息以及本次用户消息组装为完整的消息序列；
    3. 调用模型生成回答；
    4. 将本次的用户消息与模型回答追加到历史中；
    5. 裁剪历史消息，避免其无限增长。

    Args:
        session_id: 会话 ID，用于区分不同的对话上下文。
        message: 用户本次发送的消息内容。

    Returns:
        模型生成的回答文本。
    """
    # 获取指定会话的历史消息列表，若不存在则初始化为空列表。
    history = chat_history.setdefault(session_id, [])

    # 组装发送给模型的完整消息序列：
    # 系统提示词 + 历史消息 + 当前用户消息。
    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        *history,
        {
            "role": "user",
            "content": message,
        },
    ]

    # 调用模型接口生成回答。
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
    )

    # 提取模型返回的回答文本。
    # response.choices 是候选回答列表（API 支持一次生成多个候选，用 n 参数控制，
    # 这里未传 n，默认 n=1，因此列表中只有一个元素）；
    # [0] 取出第一个（默认也是唯一）候选回答；.message.content 是其文本内容。
    # 若 content 为 None 或空字符串，则通过 `or ""` 回退为空字符串，
    # 避免把 None 追加进历史消息引发问题。
    answer = response.choices[0].message.content or ""

    # 将本次对话（用户消息 + 模型回答）追加到会话历史中。
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": answer})
    
    print(history)

    # 只保留最近若干条，避免历史无限增长撑爆上下文
    if len(history) > MAX_HISTORY_MESSAGES:
        del history[: len(history) - MAX_HISTORY_MESSAGES]

    return answer
