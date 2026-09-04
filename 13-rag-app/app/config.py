import os

from dotenv import load_dotenv

load_dotenv()

from pydantic import SecretStr

# =========================
# LLM Configuration
# =========================

LLM_API_KEY = SecretStr(os.environ["LLM_API_KEY"])

LLM_BASE_URL = os.environ["LLM_BASE_URL"]

LLM_MODEL = os.environ["LLM_MODEL"]


# =========================
# Elasticsearch Configuration
# =========================

ES_URL = os.environ.get(
    "ES_URL",
    "http://127.0.0.1:9200",
)

ES_INDEX = os.environ.get(
    "ES_INDEX",
    "rag_chunks",
)


# =========================
# Logging Configuration
# =========================

# DEBUG 会把 Context 原文和完整 Prompt 打出来，只在排查时开
LOG_LEVEL = os.environ.get(
    "LOG_LEVEL",
    "INFO",
).upper()

# 留空则只输出到控制台，不写文件
LOG_FILE = os.environ.get(
    "LOG_FILE",
    "logs/rag.log",
)
