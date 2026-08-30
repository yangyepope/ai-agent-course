import requests
from langchain_core.tools import tool


""" 
@tool 这个装饰器告诉 LangChain：

这个 Python 函数可以作为 LLM 的 Tool
"""
# @tool
# def get_weather(city: str) -> str:
#     """
#     查询指定城市的天气。
#     """
#     # print(f"查询 {city} 的天气")

#     # 第一步：根据城市名查经纬度（geocoding 地理编码接口）。
#     geo_resp = requests.get(
#         "https://geocoding-api.open-meteo.com/v1/search",
#         params={"name": city, "count": 1, "language": "zh"},
#         timeout=10,
#     )
#     geo_resp.raise_for_status()
#     geo = geo_resp.json()

#     results = geo.get("results")
#     if not results:
#         return f"未找到城市：{city}"

#     loc = results[0]
#     lat, lon = loc["latitude"], loc["longitude"]
#     name = loc.get("name", city)

#     # 第二步：根据经纬度查询当前实时天气。
#     weather_resp = requests.get(
#         "https://api.open-meteo.com/v1/forecast",
#         params={
#             "latitude": lat,
#             "longitude": lon,
#             "current_weather": "true",
#         },
#         timeout=10,
#     )
#     weather_resp.raise_for_status()
#     weather = weather_resp.json()

#     cur = weather["current_weather"]
#     return (
#         f"{name} 当前温度 {cur['temperature']}°C，"
#         f"风速 {cur['windspeed']} km/h，"
#         f"天气代码 {cur['weathercode']}。"
#     )


@tool
def query_order(order_id: str) -> str:
    """
    查询指定订单的信息。
    """
    return f"订单 {order_id}：商品为 iPhone，金额 6999 元，状态为已支付。"

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