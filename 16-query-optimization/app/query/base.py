from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Query:
    """
    用户原始查询。
    """

    text: str

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class TransformedQuery:
    """
    Query Transformation 后的查询。
    """

    text: str

    original_query: str

    strategy: str

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


class BaseQueryTransformer(ABC):
    """
    Query Transformation 统一接口。
    """

    @abstractmethod
    def transform(
        self,
        query: Query,
    ) -> list[TransformedQuery]:
        """
        将一个用户 Query 转换成一个或多个检索 Query。
        """
        raise NotImplementedError
