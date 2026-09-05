class MockRetriever:

    def __init__(self):

        self.documents = [
            {
                "chunk_id": "redis-001",
                "content": (
                    "Redis 可以通过 maxmemory "
                    "参数设置最大内存限制。"
                ),
            },
            {
                "chunk_id": "redis-002",
                "content": (
                    "Redis 达到 maxmemory 后，"
                    "会根据 maxmemory-policy "
                    "决定如何处理数据。"
                ),
            },
            {
                "chunk_id": "redis-003",
                "content": (
                    "Redis 提供多种内存淘汰策略，"
                    "例如 noeviction、allkeys-lru。"
                ),
            },
            {
                "chunk_id": "redis-004",
                "content": (
                    "volatile-lru 是 Redis "
                    "提供的一种 Key 淘汰策略。"
                ),
            },
            {
                "chunk_id": "redis-005",
                "content": (
                    "RDB 是 Redis 的一种持久化方式，"
                    "通过生成数据集快照保存数据。"
                ),
            },
            {
                "chunk_id": "redis-006",
                "content": (
                    "AOF 通过记录 Redis 执行的写命令"
                    "来实现数据持久化。"
                ),
            },
            {
                "chunk_id": "redis-007",
                "content": (
                    "可以通过 Redis 配置中的 "
                    "requirepass 设置密码。"
                ),
            },
            {
                "chunk_id": "redis-008",
                "content": (
                    "Redis 支持 String、Hash、List、"
                    "Set、Sorted Set 等数据类型。"
                ),
            },
            {
                "chunk_id": "redis-009",
                "content": (
                    "Redis 主要将数据存储在内存中，"
                    "同时支持 RDB 和 AOF 持久化。"
                ),
            },
            {
                "chunk_id": "redis-010",
                "content": (
                    "Redis 主要基于内存操作，"
                    "并采用高效的数据结构和事件驱动机制。"
                ),
            },
            {
                "chunk_id": "redis-011",
                "content": (
                    "可以使用 DEL 命令删除 Redis 中的 Key。"
                ),
            },
        ]

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:

        query = query.lower()

        scored_documents = []

        for document in self.documents:

            content = document["content"].lower()

            score = 0

            for word in query.split():
                if word in content:
                    score += 1

            scored_documents.append(
                (
                    score,
                    document,
                )
            )

        scored_documents.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return [
            document
            for score, document
            in scored_documents[:top_k]
        ]
