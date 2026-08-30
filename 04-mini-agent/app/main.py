import os

from pydantic import SecretStr

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from langchain_core.messages import MessageLikeRepresentation

from app.tools import (
    calculate,
    query_order,
    query_user,
)


load_dotenv()


llm = ChatOpenAI(
    model=os.environ["LLM_MODEL"],
    api_key=SecretStr(os.environ["LLM_API_KEY"]),
    base_url=os.environ["LLM_BASE_URL"],
)


tools = [
    query_order,
    query_user,
    calculate,
]


llm_with_tools = llm.bind_tools(tools)

tool_map = {
    tool.name: tool for tool in tools
}

messages: list[MessageLikeRepresentation] = [
    (
        "system",
        """
你是一个订单系统 AI 助手。

你可以使用工具查询订单、查询用户和计算数据。

当用户的问题需要真实订单信息时，
必须调用 query_order。

当需要计算时，
调用 calculate。

请根据工具返回的数据回答问题。
""",
    ),
    (
        "human",
        # "查询订单 10001",
        """ 
        查询订单 10001，
        然后计算订单金额加上 8% 税后是多少钱。 
        """,
        
    ),
]


# while True:  生产环境绝对不能使用while true
MAX_ITERATIONS = 10
for _ in range(MAX_ITERATIONS):
    
    # 最后一次调用 LLM，得到的结果可能是：
    # 1. LLM 直接回答了问题
    # 2. LLM 调用了一个或多个工具
    response = llm_with_tools.invoke(messages)

    messages.append(response)

    if not response.tool_calls:
        print(response.content)
        break

    """ 
    取出：

    Tool Name
    +
    Tool Args
    +
    Tool Call ID
    """
    for tool_call in response.tool_calls:


        """  
        找到 Tool
        tool_name = tool_call["name"]

        tool = tool_map[tool_name]

        如果：

        tool_name = query_order

        那么：

        tool
        ↓
        真正的 query_order Tool
        """
        tool_name = tool_call["name"]

        tool = tool_map[tool_name]

        """  
        执行 Tool
        tool_result = tool.invoke(
            tool_call["args"]
        )

        相当于：

        query_order.invoke(
            {
                "order_id": "10001"
            }
        )

        得到：

        订单号：10001
        商品：iPhone
        金额：6999 元
        状态：已支付
        """
        tool_result = tool.invoke(
            tool_call["args"]
        )

        print(
            f"调用 Tool: {tool_name}"
        )

        print(
            f"Tool Result: {tool_result}"
        )

        """  
        这一步非常重要。

        为什么需要：

        tool_call_id

        因为 LLM 可能一次调用多个 Tool：

        AI
        ├── query_order
        ├── query_user
        └── calculate

        于是：

        Tool Result

        必须知道：

        我是谁的结果。

        所以：

        AI Tool Call
            id = call_001
                │
                ▼
        ToolMessage
            tool_call_id = call_001

        对应起来。 
        """
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": str(tool_result),
            }
        )

else:
    raise RuntimeError(
        "Agent exceeded maximum iterations"
    )


"""   
这才是 Agent！

现在回头看：

while True:

这就是 Agent 的核心。

一个简单 Agent 可以理解成：

while True:

    LLM()

    if 没有 Tool:
        break

    执行 Tool

    把结果返回给 LLM

非常简单。


"""


# 使用多轮工具调用
#(
#     "human",
#     """
# 查询订单 10001，
# 然后计算订单金额加上 8% 税后是多少钱。
# """,
# ), 

"""
第一轮：

LLM
 ↓
query_order(10001)

↓

订单金额：6999

第二轮：

LLM
 ↓
calculate("6999 * 1.08")

↓

7558.92

第三轮：

LLM
 ↓
最终回答

"""
