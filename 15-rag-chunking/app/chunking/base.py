from dataclasses import dataclass, field
from typing import Any


@dataclass
class Chunk:
    """
    RAG 中的一个知识块。
    """

    chunk_id: str

    content: str

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    start_index: int | None = None

    end_index: int | None = None


from abc import ABC, abstractmethod


class BaseChunker(ABC):
    """
    所有 Chunking 策略的统一接口。
    """

    @abstractmethod
    def split(
        self,
        text: str,
        metadata: dict | None = None,
    ) -> list[Chunk]:
        """
        将原始文本切分成多个 Chunk。
        """
        raise NotImplementedError



"""
现在：

BaseChunker
    │
    ├── FixedChunker
    ├── RecursiveChunker
    └── MarkdownChunker

以后再增加：

ParentChildChunker
SemanticChunker
CodeChunker

也不需要修改上层 RAG。
"""
