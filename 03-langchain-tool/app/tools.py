"""自定义工具定义：使用 @tool 装饰器把普通函数包装成 LangChain 工具。

get_weather 通过 Open-Meteo 免费接口查询真实天气（无需 API Key）。
"""

import requests
from langchain_core.tools import tool


@tool
def get_weather(city: str) -> str:
    """
    查询指定城市的真实天气。

    Args:
        city: 要查询天气的城市名称。

    Returns:
        该城市的实时天气描述文本。
    """
    print(f"查询 {city} 的天气")

    # 第一步：根据城市名查经纬度（geocoding 地理编码接口）。
    geo_resp = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1, "language": "zh"},
        timeout=10,
    )
    geo_resp.raise_for_status()
    geo = geo_resp.json()

    results = geo.get("results")
    if not results:
        return f"未找到城市：{city}"

    loc = results[0]
    lat, lon = loc["latitude"], loc["longitude"]
    name = loc.get("name", city)

    # 第二步：根据经纬度查询当前实时天气。
    weather_resp = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "current_weather": "true",
        },
        timeout=10,
    )
    weather_resp.raise_for_status()
    weather = weather_resp.json()

    cur = weather["current_weather"]
    return (
        f"{name} 当前温度 {cur['temperature']}°C，"
        f"风速 {cur['windspeed']} km/h，"
        f"天气代码 {cur['weathercode']}。"
    )


if __name__ == "__main__":
    # 只在直接运行本文件时才执行，避免被 import 时产生副作用。
    # @tool 装饰后的函数需要通过 .invoke() 调用，参数为 dict。
    print(get_weather.invoke({"city": "北京"}))
