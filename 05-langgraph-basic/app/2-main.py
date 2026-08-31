import os

from collections.abc import Sequence
from typing import Annotated, Any, Callable, TypedDict, cast

from dotenv import load_dotenv

from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

from pydantic import SecretStr

from langgraph.graph import (
    StateGraph,
    START,
    END,
)
# add_messages：LangGraph 内置的 reducer（归约器）
# 作用：节点返回的新消息会"追加"到 messages 列表末尾，而不是整体覆盖
from langgraph.graph.message import add_messages

# AIMessage：AI 生成的消息类型，只有它才携带 tool_calls 属性
from langchain_core.messages import AIMessage, HumanMessage

from app.tools import (
    query_order,
    calculate,
    query_user,
)


load_dotenv()

# 校验必需的环境变量：缺失时给出清晰报错，避免运行到一半才 KeyError
required_env = ["LLM_MODEL", "LLM_API_KEY", "LLM_BASE_URL"]
missing_env = [name for name in required_env if not os.getenv(name)]
if missing_env:
    raise RuntimeError(
        f"缺少环境变量：{', '.join(missing_env)}，请检查 .env 文件"
    )


llm = ChatOpenAI(
    model=os.environ["LLM_MODEL"],
    api_key=SecretStr(os.environ["LLM_API_KEY"]),
    base_url=os.environ["LLM_BASE_URL"],
)

tools = [
    query_order,
    calculate,
    query_user,
]

# langchain-core 1.6.1 的 bind_tools 类型签名存在误报（运行时正常），
# 用 cast 显式声明类型以消除 Pylance 告警
llm_with_tools = llm.bind_tools(
    cast(
        Sequence[dict[str, Any] | type | Callable[..., Any] | BaseTool],
        tools,
    )
)


class AgentState(TypedDict):
    # 关键点：Annotated[list, add_messages] 让节点返回的新消息"追加"到历史末尾，
    # 而不是整体覆盖。否则多轮对话中 messages 会被每一轮结果替换掉。
    messages: Annotated[list, add_messages]


# agent_node 的作用如下

"""
agent_node 是一个处理对话状态的函数，它接收包含消息列表的代理状态，
使用绑定工具的LLM生成响应，并将响应消息添加到状态中返回。

State
 ↓
读取 messages
 ↓
调用 LLM
 ↓
得到 AIMessage
 ↓
更新 State
"""


def agent_node(state: AgentState):

    response = llm_with_tools.invoke(
        state["messages"]
    )

    return {
        "messages": [
            response
        ]
    }


def tool_node(state: AgentState):

    last_message = state["messages"][-1]

    # 收窄类型：只有 AIMessage 才有 tool_calls 属性，避免 Pylance 报红
    if not isinstance(last_message, AIMessage):
        return {"messages": []}

    tool_messages = []

    for tool_call in last_message.tool_calls:

        tool_name = tool_call["name"]

        if tool_name == "query_order":

            result = query_order.invoke(
                tool_call["args"]
            )

        elif tool_name == "calculate":

            result = calculate.invoke(
                tool_call["args"]
            )
            
        elif tool_name == "query_user":

            result = query_user.invoke(
                tool_call["args"]
            )

        else:

            result = f"未知 Tool：{tool_name}"

        tool_messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": str(result),
            }
        )

    return {
        "messages": tool_messages
    }



# 定义graph 
graph_builder = StateGraph(AgentState)


# 添加agent节点Node
graph_builder.add_node(
    "agent",
    agent_node,
)

# 添加tool节点Node
graph_builder.add_node(
    "tools",
    tool_node,
)

# 现在是
""" 
Graph

agent
tools
"""

# 连接start
graph_builder.add_edge(
    START,
    "agent",
)

# 最重要的一步 条件路由
def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END

""" 
Agent
 ↓
检查 AIMessage
 ↓
有 tool_calls？
 ├── Yes → tools
 └── No → END

"""

# 添加conditional edge ,这就是LangGraph的核心功能，条件路由 Conditional Edge
graph_builder.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        END: END
    }
)   

# tool再回Agent
graph_builder.add_edge(
    "tools",
    "agent",
)

# 最终Graph
""" 
                 ┌──────────────┐
                 │    START     │
                 └──────┬───────┘
                        ↓
                 ┌──────────────┐
                 │    agent     │
                 │     LLM      │
                 └──────┬───────┘
                        ↓
                 ┌──────────────┐
                 │ Tool Call?   │
                 └──────┬───────┘
                    Yes │ No
                        │
             ┌──────────┘
             ↓
        ┌──────────────┐
        │    tools     │
        └──────┬───────┘
               │
               └──────────────→ agent


No
 ↓
END

"""

# 编译
graph = graph_builder.compile()


# 执行
from langchain_core.messages import HumanMessage

result = graph.invoke(
    {
        "messages": [
            HumanMessage(
                "查询订单 10001，然后计算订单金额加上 8% 税后是多少钱。然后再查询1001的用户信息。"
            )
        ]
    }
)

for message in result["messages"]:
    print(message.content)
    

# 执行过程类似于

"""   
HumanMessage
    │
    ▼
Agent
    │
    ▼
AIMessage
tool_calls:
query_order(10001)
    │
    ▼
Tool Node
    │
    ▼
ToolMessage
订单号：10001
商品：iPhone
金额：6999
状态：已支付
    │
    ▼
Agent
    │
    ▼
AIMessage
订单 10001 的商品是 iPhone……
    │
    ▼
END

"""    
    












