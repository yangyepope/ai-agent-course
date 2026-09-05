import os
from typing import Protocol

from app.llm.mock_llm import MockLLM
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class LLMClient(Protocol):
    """Evaluation 只依赖这一个方法。

    RAGService.answer() 和 LLMJudge.evaluate()
    都只需要「传一个 Prompt、拿一段文本」，
    所以真模型和 MockLLM 可以互换。
    """

    def chat(
        self,
        prompt: str,
    ) -> str:
        ...


class OpenAILLM:
    """把 OpenAI 兼容接口包成 chat(prompt) -> str。

    13-rag-app 里的 LLMService 收的是 messages 列表，
    而 Evaluation 这边（RAGService.answer / LLMJudge）
    只想传一个 Prompt 字符串，
    所以这里做一层薄适配。
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
    ):
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )

        self.model = model

    def chat(
        self,
        prompt: str,
    ) -> str:

        response = (
            self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                # Evaluation 必须可复现，
                # temperature 一定要 0。
                temperature=0,
            )
        )

        return (
            response.choices[0].message.content
            or ""
        )


def create_llm() -> LLMClient:
    """三个环境变量齐了就用真模型，缺任何一个都降级到 MockLLM。"""

    api_key = os.environ.get(
        "LLM_API_KEY"
    )

    base_url = os.environ.get(
        "LLM_BASE_URL"
    )

    model = os.environ.get(
        "LLM_MODEL"
    )

    # base_url 也必须检查。
    # 少了它 os.environ.get 会返回 None，
    # 而 OpenAILLM 声明的是 str，类型直接对不上；
    # 更麻烦的是运行时不报错，
    # 而是默默打到 api.openai.com 然后 401，
    # 排查半天才发现只是漏配了中转地址。
    if not api_key or not base_url or not model:

        print(
            "[warn] 未检测到 LLM_API_KEY / "
            "LLM_BASE_URL / LLM_MODEL，"
            "已降级为 MockLLM，"
            "Faithfulness / Correctness 分数无意义。"
        )

        return MockLLM()

    return OpenAILLM(
        api_key=api_key,
        base_url=base_url,
        model=model,
    )
