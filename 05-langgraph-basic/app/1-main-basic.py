"""
LangGraph 基础示例：第一个最小可运行的图（Graph）

本示例演示 LangGraph 的核心概念：
1. State（状态）    —— 在节点之间流动的数据结构
2. Node（节点）     —— 图中的执行单元（一个函数）
3. Edge（边）       —— 节点之间的连接关系，决定执行顺序
4. Compile（编译）  —— 将图结构编译为可执行对象
5. Invoke（调用）   —— 传入初始状态，启动图执行

执行流程（一个简单的线性图）：
    START --> hello节点 --> END
    初始状态 {"messages": []} 从 START 流入
    hello 节点把 "Hello" 追加到 messages 中
    最终返回 {"messages": ["Hello"]}
"""

from typing import TypedDict

# StateGraph：图构建器，用于组装节点和边
# START / END：图的内置入口节点 / 出口节点
from langgraph.graph import StateGraph, START, END


# ---------------------------------------------------------------------------
# 1. 定义 State（图的状态结构）
# ---------------------------------------------------------------------------
# LangGraph 中的"状态"是一个共享数据容器，会在节点之间传递并逐步更新。
# 这里用 TypedDict 声明状态的结构，让每个节点都能看到并修改状态。
class AgentState(TypedDict):
    # messages 用于存放对话消息列表，图执行过程中会被节点不断追加内容
    messages: list


# ---------------------------------------------------------------------------
# 2. 构建图（添加节点和边）
# ---------------------------------------------------------------------------
# 创建图构建器，必须传入状态结构 AgentState 作为参数。
# 注意：不能用旧版的 StateGraph[AgentState]() 泛型下标写法（langgraph 1.x 已移除）
graph_builder = StateGraph(AgentState)


# ---------------------------------------------------------------------------
# 3. 定义节点（Node）
# ---------------------------------------------------------------------------
# 节点就是一个普通的 Python 函数：
#   - 入参：当前的状态（state）
#   - 返回值：一个字典，表示要对状态做的"增量更新"（会被合并回状态中）
def hello_node(state: AgentState):
    print("Hello LangGraph")

    # 返回的字典会与当前状态合并：
    # 把 "Hello" 追加到已有的 messages 列表末尾
    return {
        "messages": state["messages"]
        + ["Hello"]
    }


# 把节点注册进图中，并起一个名字 "hello"
# 之后就可以通过这个名字来引用该节点
graph_builder.add_node(
    "hello",
    hello_node,
)


# ---------------------------------------------------------------------------
# 4. 添加边（Edge），连接节点执行顺序
# ---------------------------------------------------------------------------
# 从内置入口 START 连接到 "hello" 节点 —— 图开始执行时首先运行 hello
graph_builder.add_edge(
    START,
    "hello",
)

# 从 "hello" 节点连接到内置出口 END —— hello 执行完毕后图结束
graph_builder.add_edge(
    "hello",
    END,
)


# ---------------------------------------------------------------------------
# 5. 编译图
# ---------------------------------------------------------------------------
# compile() 将上面的节点、边结构编译成一个可调用的图对象
# 编译后可以检查图结构（graph.get_graph()）或直接执行
graph = graph_builder.compile()


# ---------------------------------------------------------------------------
# 6. 执行图（invoke）
# ---------------------------------------------------------------------------
# invoke 接收初始状态作为输入，沿着图的边依次执行节点，
# 最后返回经过所有节点更新后的最终状态。
# 流程：{"messages": []} --START--> hello节点追加"Hello" --> END
# 结果：{"messages": ["Hello"]}
result = graph.invoke(
    {
        "messages": []
    }
)

print(result)



# LangGraph 最基础骨架
""" 
现在停下来理解这个过程

你刚刚做了：

1. 定义 State

2. 定义 Node

3. 添加 Node

4. 添加 Edge

5. compile

6. invoke

也就是：

State
 ↓
Graph
 ↓
Node
 ↓
Edge
 ↓
Compile
 ↓
Invoke

这就是 LangGraph 最基础的骨架。
"""