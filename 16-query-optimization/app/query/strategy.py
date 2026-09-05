from enum import Enum


class QueryStrategy(str, Enum):

    ORIGINAL = "original"

    REWRITE = "rewrite"

    MULTI_QUERY = "multi_query"

    HYDE = "hyde"
