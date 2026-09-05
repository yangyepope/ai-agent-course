import json


class MockLLM:
    """没有配 LLM_API_KEY 时的替身。

    目的只有一个：让整条 Evaluation Pipeline
    在不花钱、不联网的情况下也能跑通，
    方便先验证代码结构是否正确。

    注意：它给出的 Faithfulness / Correctness
    是假的，不能用来评价真实 RAG 质量。
    """

    # RAGService.answer() 和 LLMJudge.evaluate()
    # 用的是同一个 chat() 接口，
    # 所以这里靠 Prompt 里的标记区分是哪一种调用。
    JUDGE_MARKER = "请只返回 JSON"

    def chat(
        self,
        prompt: str,
    ) -> str:

        if self.JUDGE_MARKER in prompt:
            return self._fake_judge()

        return self._fake_answer(
            prompt
        )

    @staticmethod
    def _fake_answer(
        prompt: str,
    ) -> str:

        return (
            "[MockLLM] 这是一个占位回答，"
            "未接入真实模型。"
        )

    @staticmethod
    def _fake_judge() -> str:

        # 故意包上 ```json 围栏，
        # 顺便验证 LLMJudge 的解析容错。
        payload = json.dumps(
            {
                "answer_relevance": 0.5,
                "faithfulness": 0.5,
                "correctness": 0.5,
                "reason": (
                    "MockLLM 未接入真实模型，"
                    "分数无意义。"
                ),
            },
            ensure_ascii=False,
        )

        return (
            "```json\n"
            f"{payload}\n"
            "```"
        )
