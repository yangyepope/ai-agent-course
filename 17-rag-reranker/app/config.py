import os

from dotenv import load_dotenv

load_dotenv()


LLM_API_KEY = os.getenv(
    "LLM_API_KEY",
    "",
)

LLM_BASE_URL = os.getenv(
    "LLM_BASE_URL",
    "",
)

LLM_MODEL = os.getenv(
    "LLM_MODEL",
    "",
)


EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "BAAI/bge-small-zh-v1.5",
)


RERANKER_MODEL = os.getenv(
    "RERANKER_MODEL",
    "BAAI/bge-reranker-base",
)


VECTOR_TOP_K = int(
    os.getenv(
        "VECTOR_TOP_K",
        "10",
    )
)


RERANK_TOP_N = int(
    os.getenv(
        "RERANK_TOP_N",
        "5",
    )
)
