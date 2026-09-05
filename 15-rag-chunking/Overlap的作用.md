例如：

chunk_size = 100
overlap = 20

那么：

Chunk 1
0 ─────────────────── 100

Chunk 2
                  80 ─────────────────── 180

Chunk 3
                                    160 ───────────────

也就是：

Chunk 1
[--------------------]

             Chunk 2
             [--------------------]

                          Chunk 3
                          [--------------------]

重叠部分：

20

为什么需要 Overlap？

因为一个语义可能刚好位于边界：

Chunk 1
Redis 可以通过 maxmemory

↓

Chunk 2
参数设置最大内存。

如果完全没有 overlap：

知识被拆散

加入 overlap：

Chunk 1
Redis 可以通过 maxmemory 参数

Chunk 2
maxmemory 参数设置最大内存。

上下文连续性更好。
