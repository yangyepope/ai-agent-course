from app.query.base import Query
from app.query.rewrite import QueryRewriter


def main():

    query = Query(
        text="Redis 为什么会自动删除 Key？"
    )

    rewriter = QueryRewriter()

    results = rewriter.transform(
        query
    )

    print()
    print("=" * 60)
    print("Original Query")
    print("=" * 60)

    print(query.text)

    print()
    print("=" * 60)
    print("Rewritten Query")
    print("=" * 60)

    for result in results:

        print(result.text)


if __name__ == "__main__":
    main()
