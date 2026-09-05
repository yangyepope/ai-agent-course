"""Chunking 策略的测试。

当前这两个用例属于 **冒烟测试（smoke test）**：
只保证「能跑通、不崩、产出结构合法」，
不保证「切得对」。

    冒烟测试     →  代码没写错（能跑）
    行为测试     →  策略没设计错（切得对）
                    └──► 见文件末尾 TODO
"""

from app.chunking.fixed import (
    FixedChunker,
)
from app.chunking.recursive import (
    RecursiveChunker,
)


def test_fixed_chunker():
    """FixedChunker：定长切分，能切出多块且元数据正确传递。

    实际切分结果（chunk_size=20, overlap=5，原文 43 字）：

        [  0: 20] 'Redis 是一个高性能数据库。Redi'
        [ 15: 35] '。Redis 支持多种数据类型。Redi'
        [ 30: 43] '。Redis 支持持久化。'
                ↑
        每块起点 = 上一块起点 + (chunk_size - overlap) = +15
        所以相邻块有 5 个字符重叠

    注意第 1 块结尾把 "Redis" 切成了 "Redi" ——
    这正是定长切分的固有缺陷，也是 RecursiveChunker 存在的理由。
    """

    text = (
        "Redis 是一个高性能数据库。"
        "Redis 支持多种数据类型。"
        "Redis 支持持久化。"
    )

    chunker = FixedChunker(
        chunk_size=20,
        overlap=5,
    )

    chunks = chunker.split(
        text,
        metadata={
            "source": "redis.md"
        },
    )

    # 验点 1：确实发生了切分。
    # 43 字 / 步长 15 → 3 块。
    # 如果哪天 while 循环写错（比如忘了 start += step），
    # 这里会退化成 1 块或死循环。
    assert len(chunks) > 1

    for chunk in chunks:

        # 验点 2：没有空块。
        # fixed.py 里 strip() 之后有 `if content:` 判断，
        # 全空白的片段会被丢弃 —— 这行守住那个逻辑。
        assert chunk.content

        # 验点 3：metadata 透传。
        # 切分器必须把调用方传进来的 source 原样带到每一块上，
        # 否则 RAG 检索到 chunk 之后就说不出"这句话出自哪个文档"，
        # 引用来源功能直接废掉。
        assert (
            chunk.metadata["source"]
            == "redis.md"
        )


def test_recursive_chunker():
    """RecursiveChunker：按分隔符优先级递归切分，尽量不切断语义。

    实际切分结果（chunk_size=50, overlap=10）：

        len=44  'Redis 是一个高性能数据库。\\n\\nRedis 支持 String、Hash、List。'
        len=33  'Hash、List。Redis 支持 RDB 和 AOF 持久化。'
                 └──────┘ ← 来自上一块尾部的 10 字符 overlap
        len=38  '和 AOF 持久化。Redis 可以通过 maxmemory\\n设置最大内存。'

    和 FixedChunker 的关键差别：
    切口落在 "。" 和 "\\n\\n" 上，没有把词切断。
    """

    text = """
Redis 是一个高性能数据库。

Redis 支持 String、Hash、List。

Redis 支持 RDB 和 AOF 持久化。

Redis 可以通过 maxmemory
设置最大内存。
"""

    chunker = RecursiveChunker(
        chunk_size=50,
        overlap=10,
    )

    chunks = chunker.split(
        text,
        metadata={
            "source": "redis.md"
        },
    )

    # 验点 1：递归确实终止并产出了多块。
    # _recursive_split 是递归函数，
    # 写错了要么无限递归（RecursionError），
    # 要么整段原样返回（1 块）—— 这行同时守住这两种崩法。
    assert len(chunks) > 1

    for chunk in chunks:

        # 验点 2：没有空块。
        # split() 里对每个 raw_chunk 做了 strip() + continue，
        # 因为按 "\\n\\n" 切完会产生大量空字符串。
        assert chunk.content


# ==========================================================
# TODO：这两个用例没有覆盖的行为
# ==========================================================
"""
上面的断言全部通过，但下面这些「切得对不对」一个都没验：

    ┌─ FixedChunker
    │   ✗ 每块长度 <= chunk_size
    │   ✗ 相邻块真的重叠了 overlap 个字符   ← overlap 是它唯一的核心功能
    │   ✗ chunk_id 唯一
    │   ✗ start_index / end_index 与 content 对得上
    │
    └─ RecursiveChunker
        ✗ 每块长度 <= chunk_size            ← 实测会超，见下
        ✗ 切口优先落在 "\\n\\n" 上           ← 递归切分的全部意义
        ✗ metadata 透传（fixed 验了，这里漏了，不对称）

其中「长度 <= chunk_size」这条现在加上去会**直接失败**：

    text = "\\n\\n".join(["A"*48, "B"*48, "C"*48])
    RecursiveChunker(chunk_size=50, overlap=10).split(text)
        ↓
    len= 48   ✓
    len= 58   ✗ 超过 chunk_size
    len= 58   ✗ 超过 chunk_size

原因见 recursive.py 的 _apply_overlap()：
它是「先切好，再把前一块的尾巴拼到后一块头上」，
拼接时没有重新裁剪，所以长度变成 chunk_size + overlap。

而 fixed.py 的做法是「滑动窗口」——
overlap 体现在起点后退（start += chunk_size - overlap），
长度天然不会超。两个类对 overlap 的实现方式根本不同。
"""


def test_markdown_chunker():

    from app.chunking.markdown import (
        MarkdownChunker,
    )

    text = """
# Redis

Redis 是一个高性能内存数据库。

## 数据类型

Redis 支持 String、Hash、List。

## 持久化

Redis 支持 RDB 和 AOF。
"""

    chunker = MarkdownChunker()

    chunks = chunker.split(
        text,
        metadata={
            "source": "redis.md"
        },
    )

    assert len(chunks) == 3

    assert (
        chunks[0].metadata["section"]
        == "Redis"
    )

    assert (
        chunks[1].metadata["section"]
        == "数据类型"
    )

    assert (
        chunks[2].metadata["section"]
        == "持久化"
    )
