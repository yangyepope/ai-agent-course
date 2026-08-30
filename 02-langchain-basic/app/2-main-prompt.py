from langchain_openai import ChatOpenAI

from dotenv import load_dotenv
from pydantic import SecretStr
import os
from langchain_core.messages import (SystemMessage, HumanMessage, AIMessage)
from langchain_core.prompts import ChatPromptTemplate


load_dotenv()


def _require(name: str) -> str:
    """读取环境变量，缺失时抛出异常，返回类型固定为 str。

    Args:
        name: 环境变量名称。

    Returns:
        环境变量的值（保证非空字符串）。
    """
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not configured")
    return value


llm = ChatOpenAI(
    model=_require("LLM_MODEL"),
    api_key=SecretStr(_require("LLM_API_KEY")),
    base_url=_require("LLM_BASE_URL"),
)


prompt = ChatPromptTemplate.from_messages([
    (
        "system", "你是一名资深 Java 后端工程师。"
    ),
    (
        "human",
            """
请介绍一下 {technology}。

要求：
1. 解释基本原理
2. 说明使用场景
3. 给出一个实际案例
""",
    )
])

# # messages = prompt.invoke({"technology": "Redis"})
# # print(messages)

# messages = prompt.invoke({"technology": "Redis"})
# response = llm.invoke(messages)
# print(response.content)

# 1. 只执行 prompt.invoke
messages = prompt.invoke({"technology": "Redis"})
print("--- 打印 messages 的内容 ---")
print(type(messages))
print(messages)

print("\n" + "="*50 + "\n")

# 2. 执行 llm.invoke
response = llm.invoke(messages)
print("--- 打印 response.content 的内容 ---")
print(type(response.content))
print(response.content)
print("\n" + "="*50 + "\n")

chain = prompt | llm
response = chain.invoke({"technology": "Redis"})
print("\n" + "="*50 + "\n")
print("--- 打印 chain.invoke 的内容 ---")
print(type(response))
"""
LCEL
LangChain Expression Language。

不要把它理解成普通 Python 的“或”。

这里表示：

前一个组件的输出
        ↓
后一个组件的输入

所以：

chain = prompt | llm

相当于：

Prompt
  ↓
Messages
  ↓
LLM
  ↓
AIMessage

这就是 Pipeline。


"""





"""
technology = Redis
       ↓
PromptTemplate
       ↓
System + Human Message
       ↓
ChatModel
       ↓
LLM
       ↓
AIMessage


"""






"""
你会发现：

PromptTemplate
     ↓
invoke()
     ↓
Messages

它还没有调用 LLM。
"""


"""
很多初学者会混：

Prompt

和：

LLM

实际上：

Prompt
 ↓
负责构造输入

LLM
 ↓
负责生成输出

所以：

Prompt
   ↓
Messages
   ↓
LLM
   ↓
AIMessage
"""