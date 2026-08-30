"""演示 @tool 装饰器生成的工具对象所携带的属性。"""

from pydantic import SecretStr

# from app.tools import get_weather
from app.tools import query_order


# get_weather 被 @tool 装饰后，是一个 LangChain Tool 对象，
# 自动拥有了 .name、.description、.args 等属性。
# print(get_weather)             # 工具对象本身
# print(get_weather.name)        # 工具名（来自函数名）
# print(get_weather.description) # 工具描述（来自 docstring）
# print(get_weather.args)        # 工具参数 schema（来自函数签名）


print(query_order)             # 工具对象本身
print(query_order.name)        # 工具名（来自函数名）
print(query_order.description) # 工具描述（来自 docstring）
print(query_order.args)        # 工具参数 schema（来自函数签名）



""" 
用户提问「北京天气怎么样」
   ↓
LLM 判断需要调用 get_weather 工具
   ↓
LLM 生成工具调用请求 {"city": "北京"}
   ↓
程序执行 get_weather("北京")
   ↓
把结果回传给 LLM，生成最终回答

"""




""" 
Python Function
      ↓
LangChain Tool
      ↓
Tool Schema
      ↓
LLM
"""


#  什么是 tool schema？就是工具的参数定义。

""" 
假设：

@tool
def query_order(order_id: str) -> str:
    ...

那么 LLM 需要知道：

Tool:
query_order

参数:
order_id
类型:
string

这就是：

Tool Schema

它实际上描述了：

Tool 能做什么
+
需要什么参数

"""


import os 
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
# from app.tools import get_weather
from app.tools import query_order

load_dotenv()

llm = ChatOpenAI(
    model=os.environ["LLM_MODEL"],
    api_key=SecretStr(os.environ["LLM_API_KEY"]),
    base_url=os.environ["LLM_BASE_URL"],
)   

# bind_tools() 方法把工具绑定到 LLM 上，返回一个新的 LLM 对象。是一个非常重要的方法
# 它的意思是不是立即执行Tool，而是告诉LLM：你可以调用这个Tool，Tool的参数schema是这样的。
""" 
get_weather
查询指定城市的天气。

Args:
    city: 要查询天气的城市名称。

Returns:
    该城市的天气描述文本。
{'city': {'title': 'City', 'type': 'string'}}

"""


# 第一步：把工具绑定到 LLM 上，返回一个新的 LLM 对象

# llm_with_tools = llm.bind_tools([get_weather])
llm_with_tools = llm.bind_tools([query_order])

"""
绑定工具后，LLM可以调用这些工具
[
  {
    "type": "function",
    "function": {
      "name": "get_weather",
      "description": "查询指定城市的天气。",
      "parameters": {
        "type": "object",
        "properties": {
          "city": {"type": "string"}
        },
        "required": ["city"]
      }
    }
  }
]


"""

# 第二步：调用 LLM，发起真正的 API 请求
response = llm_with_tools.invoke("查询一下订单 10001")

"""
invoke("武汉今天天气怎么样") 发起真正的 API 请求
invoke 内部，LangChain 把消息和工具清单一起，组装成一次 OpenAI 兼容的 HTTP 请求发出去。大致等价于（伪代码）：

请求体 = {
    "model": "qwen...",
    "messages": [
        {"role": "user", "content": "武汉今天天气怎么样"}
    ],
    "tools": [  # ← bind_tools 挂载的工具清单在这里带上
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "查询指定城市的天气。",
                "parameters": {...city: string...}
            }
        }
    ]
}

"""


"""
执行 Tool
get_weather.invoke(...)

意思：

真正执行 Python 函数

所以：

bind_tools
    ↓
Tool Definition
    ↓
LLM

invoke
    ↓
真正执行 Tool

一定不要混淆。
"""

print("=================================")

print("AIMessage:", response)


print("=================================")
# response =  get_weather.invoke({"city": "北京"})

# print("Tool Response:", response)

print("AI Response:")
print(response)
print("-------------")
print("\nTool Calls:")
print(response.tool_calls)


# 第三步： 取出第一个工具调用

# 获取工具调用
tool_call = response.tool_calls[0]

print(">>>>>>>>>>>>>>>>")
print(tool_call)

# 第四步： 真正执行工具，获取结果，查询天气
# 这个是执行工具的地方
# tool_result = get_weather.invoke(
#     tool_call["args"]
# )

tool_result = query_order.invoke(
    tool_call["args"])

print("tool result:", tool_result)

# 当前流程是:
"""
LLM
 ↓
tool_calls
 ↓
Python
 ↓
Tool
"""

# 把 Tool Result 发送回 LLM
""" 
我们需要：

HumanMessage
AIMessage
ToolMessage

完整过程：

Human
 ↓
AI
 ↓
ToolMessage
 ↓
AI

代码：如下

"""


# 第五步： 
from langchain_core.messages import ToolMessage
tool_message = ToolMessage(
    content=tool_result,
    tool_call_id=tool_call["id"],
)

messages = [
    {
        "role": "user",
        "content": "查询一下订单 10001",
    },
    response,
    tool_message,
]

final_response = llm_with_tools.invoke(messages)

print(final_response.content)


"""
用户：
北京今天的天气怎么样？

↓

LLM：
我要调用 get_weather

↓

Python：
get_weather("北京")

↓

Tool：
北京今天晴天，温度 30°C

↓

LLM：
北京今天晴天，温度 30°C，空气质量良好。

"""



"""
完整过程：

                 User
                   │
                   ▼
                  LLM
                   │
             Tool Call
                   │
                   ▼
             Python Tool
                   │
             get_weather()
                   │
                   ▼
              Tool Result
                   │
                   ▼
                  LLM
                   │
                   ▼
                Answer

这就是 Agent 的核心循环雏形。
"""