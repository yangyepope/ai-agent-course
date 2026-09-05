# 但是 Fixed Chunk 有一个问题

假设原文：
``` text
# Redis

Redis 是一个高性能数据库。

## 数据类型

Redis 支持 String、Hash、List。

## 持久化

Redis 支持 RDB 和 AOF。

## 内存管理

Redis 可以通过 maxmemory
设置最大内存。

Fixed Chunk 不关心：

#
##
###

它只看：

字符数量
```

# 可能出现：

Chunk 1

# Redis

Redis 是一个高性能数据库。

## 数据类型

Redis 支持

Chunk 2：

String、Hash、List。

## 持久化

Redis 支持 RDB 和 AOF。

## 内存管理

Chunk 3：

Redis 可以通过 maxmemory
设置最大内存。

这显然不够理想。


# Recursive Chunking

所以我们开始实现：

Recursive Chunking

思想是：

优先按照大的语义边界切
        ↓
如果太大
        ↓
继续按照更小边界切

例如：

段落
 ↓
句子
 ↓
单词
 ↓
字符

可以理解成：

Paragraph
    ↓
Sentence
    ↓
Word
    ↓
Character
