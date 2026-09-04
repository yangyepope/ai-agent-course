import time

from app.config import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
)
from app.logging_config import get_logger
from openai import OpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
)

logger = get_logger(__name__)


class LLMService:
    def __init__(self):
        self.client = OpenAI(
            api_key=LLM_API_KEY.get_secret_value(),
            base_url=LLM_BASE_URL,
        )

        self.model = LLM_MODEL

    def chat(
        self,
        messages: list[ChatCompletionMessageParam],
    ) -> str:

        # Prompt 只在 DEBUG 打：它包含知识库原文，又长又可能敏感
        logger.debug(
            "LLM 请求 model=%s messages=%s",
            self.model,
            [
                {
                    "role": message.get("role"),
                    "content": message.get("content"),
                }
                for message in messages
            ],
        )

        started = time.perf_counter()

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0,
            )
        except Exception:
            elapsed_ms = (time.perf_counter() - started) * 1000

            # exception() 会把 traceback 一起写进日志
            logger.exception(
                "LLM 调用失败 | model=%s | %.0fms",
                self.model,
                elapsed_ms,
            )
            raise

        elapsed_ms = (time.perf_counter() - started) * 1000

        usage = response.usage

        logger.info(
            "LLM 生成完成 | model=%s | %.0fms | token 输入 %s 输出 %s",
            self.model,
            elapsed_ms,
            usage.prompt_tokens if usage else "?",
            usage.completion_tokens if usage else "?",
        )

        answer = response.choices[0].message.content or ""

        if not answer:
            logger.warning(
                "LLM 返回空内容 | finish_reason=%s",
                response.choices[0].finish_reason,
            )

        logger.debug("LLM 回答：%s", answer)

        return answer
