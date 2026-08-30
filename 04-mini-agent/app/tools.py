from langchain_core.tools import tool


@tool
def query_order(order_id: str) -> str:
    """
    查询指定订单的信息。

    参数:
    order_id: 订单 ID
    """
    orders = {
        "10001": {
            "product": "iPhone",
            "amount": 6999,
            "status": "已支付",
        },
        "10002": {
            "product": "MacBook",
            "amount": 12999,
            "status": "待支付",
        },
    }

    order = orders.get(order_id)

    if not order:
        return f"订单 {order_id} 不存在"

    return (
        f"订单号：{order_id}，"
        f"商品：{order['product']}，"
        f"金额：{order['amount']} 元，"
        f"状态：{order['status']}"
    )


@tool
def calculate(expression: str) -> str:
    """
    计算数学表达式。

    例如:
    100 + 200
    6999 * 1.08
    """
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"计算失败: {e}"


@tool
def query_user(user_id: str) -> str:
    """
    查询用户信息。
    """
    users = {
        "1": "张三",
        "2": "李四",
    }

    user = users.get(user_id)

    if not user:
        return "用户不存在"

    return f"用户 ID：{user_id}，用户名：{user}"