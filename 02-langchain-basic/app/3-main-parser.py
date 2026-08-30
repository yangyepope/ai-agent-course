from langchain_openai import ChatOpenAI

from dotenv import load_dotenv
from pydantic import SecretStr
import os
from langchain_core.messages import (SystemMessage, HumanMessage, AIMessage)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

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
        # "system", "你是一名资深 Java 后端工程师。"
        "system","你是一名资深 AI Agent 开发工程师。"
    ),
    (
        "human",
            """
请介绍一下 {technology}。

要求：
1. 解释基本原理
2. 说明使用场景
3. 给出一个实际案例
4. 使用 {language} 语言给出代码示例
""",
    )
])

parser = StrOutputParser()

chain = prompt | llm | parser

""" 
现在整个流程：
Prompt
   ↓
ChatModel
   ↓
AIMessage
   ↓
StrOutputParser
   ↓
String
"""

result =  chain.invoke({"technology": "LangChain","language":"Python"})

print(result)

""" 
用户参数
   │
   ▼
┌──────────────┐
│    Prompt    │
│ technology   │
└──────┬───────┘
       │
       ▼
SystemMessage
HumanMessage
       │
       ▼
┌──────────────┐
│     LLM      │
└──────┬───────┘
       │
       ▼
  AIMessage
       │
       ▼
┌──────────────┐
│    Parser    │
└──────┬───────┘
       │
       ▼
     String
"""



# 今天你需要记住的 8 个东西
""" 
① ChatModel

LangChain 对聊天模型的抽象。


② Message

System / Human / AI / Tool


③ PromptTemplate

负责生成 Prompt / Message。


④ Output Parser

负责把 LLM 输出转换成业务需要的格式。


⑤ Runnable

可以被调用、组合的组件。


⑥ Chain

多个 Runnable 组合起来。


⑦ LCEL

使用 | 组合 Runnable。


⑧ LangChain

提供这些组件和编排能力。
"""