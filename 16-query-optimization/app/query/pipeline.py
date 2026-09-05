from app.query.base import (
    BaseQueryTransformer,
    Query,
    TransformedQuery,
)


class QueryPipeline:

    def __init__(
        self,
        transformer: BaseQueryTransformer,
    ):

        self.transformer = transformer

    def process(
        self,
        query_text: str,
    ) -> list[TransformedQuery]:

        query = Query(
            text=query_text
        )

        return self.transformer.transform(
            query
        )


from app.query.pipeline import (
    QueryPipeline,
)
from app.query.rewrite import (
    QueryRewriter,
)

pipeline = QueryPipeline(
    transformer=QueryRewriter()
)

results = pipeline.process(
    "Redis 为什么会自动删除 Key？"
)
