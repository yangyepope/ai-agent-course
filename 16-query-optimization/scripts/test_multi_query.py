from app.query.base import Query
from app.query.multi_query import (
    MultiQueryTransformer,
)


def main():

    query = Query(
        text="Redis 为什么会自动删除 Key？"
    )

    transformer = MultiQueryTransformer(
        query_count=5
    )

    results = transformer.transform(
        query
    )

    print()
    print("=" * 60)
    print("Original Query")
    print("=" * 60)

    print(query.text)

    print()
    print("=" * 60)
    print("Generated Queries")
    print("=" * 60)

    for index, result in enumerate(
        results,
        start=1,
    ):

        print(
            f"{index}. {result.text}"
        )


if __name__ == "__main__":
    main()
