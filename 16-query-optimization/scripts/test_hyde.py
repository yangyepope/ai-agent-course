from app.query.base import Query
from app.query.hyde import (
    HyDETransformer,
)


def main():

    query = Query(
        text="Redis 为什么会自动删除 Key？"
    )

    transformer = HyDETransformer()

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
    print("Hypothetical Document")
    print("=" * 60)

    print(results[0].text)


if __name__ == "__main__":
    main()
