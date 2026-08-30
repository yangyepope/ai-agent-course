import os

from dotenv import load_dotenv


load_dotenv()


def _require(name: str) -> str:

    value = os.getenv(name)

    if not value:
        raise RuntimeError(f"{name} is not configured")

    return value


LLM_API_KEY: str = _require("LLM_API_KEY")
LLM_BASE_URL: str = _require("LLM_BASE_URL")
LLM_MODEL: str = _require("LLM_MODEL")
