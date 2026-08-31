from langchain_core.tools import tool


# def get_weather(city: str) -> str:
#     """
#     查询指定城市的天气。
#     """
#     print(f"查询 {city} 的天气")
#     return f"{city}今天晴天，温度 30°C，空气质量良好。"


# get_weather("北京")



""" 
@tool 这个装饰器告诉 LangChain：

这个 Python 函数可以作为 LLM 的 Tool
"""
@tool
def get_weather(city: str) -> str:
    """
    查询指定城市的天气。
    """
    print(f"查询 {city} 的天气")
    return f"{city}今天晴天，温度 30°C，空气质量良好。"


""" 
这里的：

查询指定城市的天气。

不是普通注释那么简单。

它会成为 Tool 的描述信息。

LLM 需要知道：

Tool 名字：
get_weather

作用：
查询指定城市的天气

参数：
city
类型：
string

所以 Tool 最终可以抽象成：

{
  "name": "get_weather",
  "description": "查询指定城市的天气",
  "parameters": {
    "city": {
      "type": "string"
    }
  }
}
"""