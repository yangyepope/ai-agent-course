"""演示 @tool 装饰器生成的工具对象所携带的属性。"""

from pydantic import SecretStr

from app.tools import get_weather


# get_weather 被 @tool 装饰后，是一个 LangChain Tool 对象，
# 自动拥有了 .name、.description、.args 等属性。
print(get_weather)             # 工具对象本身
print(get_weather.name)        # 工具名（来自函数名）
print(get_weather.description) # 工具描述（来自 docstring）
print(get_weather.args)        # 工具参数 schema（来自函数签名）





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
get_weather
查询指定城市的天气。

Args:
    city: 要查询天气的城市名称。

Returns:
    该城市的天气描述文本。
{'city': {'title': 'City', 'type': 'string'}}

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
from app.tools import get_weather

load_dotenv()

llm = ChatOpenAI(
    model=os.environ["LLM_MODEL"],
    api_key=SecretStr(os.environ["LLM_API_KEY"]),
    base_url=os.environ["LLM_BASE_URL"],
)   

# bind_tools() 方法把工具绑定到 LLM 上，返回一个新的 LLM 对象。是一个非常重要的方法
# 它的意思是不是立即执行Tool，而是告诉LLM：你可以调用这个Tool，Tool的参数schema是这样的。
llm_with_tools = llm.bind_tools([get_weather])

response = llm_with_tools.invoke("北京今天天气怎么样")

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
get_weather.invoke({"city": "北京"})