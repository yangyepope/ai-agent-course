你现在看到：

Prompt
LLM
Parser

它们都可以参与这种链式调用。

你可以暂时把：

Runnable

理解成：

“一个可以接收输入、处理输入、产生输出的组件。”

例如：

Prompt
输入：{"technology": "Redis"}
输出：Messages

然后：

LLM
输入：Messages
输出：AIMessage

然后：

Parser
输入：AIMessage
输出：String

于是：

Runnable
    ↓
Runnable
    ↓
Runnable

组成 Chain。