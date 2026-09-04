import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

load_dotenv()


llm = ChatOpenAI(
    model=os.environ["LLM_MODEL"],
    api_key=SecretStr(os.environ["LLM_API_KEY"]),
    base_url=os.environ["LLM_BASE_URL"],
)


# response = llm.invoke("你好，请介绍一下自己。")

messages = [
    SystemMessage(content="你是一名资深 Java 后端工程师。"),
    HumanMessage(content="Redis为什么这么快呀。"),
]

response = llm.invoke(messages)
print(response.content)

"""
我们不再直接关心：

HTTP POST
JSON
choices
message

而是：

ChatModel
    ↓
invoke()
    ↓
AIMessage

所以：

llm.invoke("你好")

可以理解成：

输入
 ↓
ChatModel
 ↓
LLM
 ↓
AIMessage


LangChain 把不同模型统一成了类似的接口。

例如：

ChatOpenAI
ChatDeepSeek
ChatOllama
ChatAnthropic
...

你可以把它们理解成：

        ChatModel
           │
     ┌─────┼─────┐
     ↓     ↓     ↓
 OpenAI  DeepSeek Ollama

你的上层应用可以使用：

llm.invoke(...)


LangChain 把消息抽象成对象：

BaseMessage
    │
    ├── SystemMessage
    ├── HumanMessage
    ├── AIMessage
    └── ToolMessage

对应我们之前学习的：

System
User
Assistant
Tool


"""

# print(response)
