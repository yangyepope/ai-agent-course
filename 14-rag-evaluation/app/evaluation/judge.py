import json
import re


class LLMJudge:

    def __init__(
        self,
        llm,
    ):
        self.llm = llm

    def evaluate(
        self,
        question: str,
        context: str,
        answer: str,
        ground_truth: str,
    ) -> dict:

        prompt = f"""
你是一名严格的 RAG Evaluation 专家。

请评价一个 RAG 系统生成的答案。

====================
Question
====================

{question}

====================
Context
====================

{context}

====================
Ground Truth
====================

{ground_truth}

====================
Answer
====================

{answer}

====================
Evaluation
====================

请评价以下三个指标。

1. answer_relevance

回答是否真正回答了 Question。

2. faithfulness

Answer 中的陈述是否能够从 Context
中得到支持。

3. correctness

Answer 是否与 Ground Truth
表达的事实一致。

每个指标评分范围：

0.0 ~ 1.0

请只返回 JSON：

{{
    "answer_relevance": 0.0,
    "faithfulness": 0.0,
    "correctness": 0.0,
    "reason": "评价原因"
}}
"""

        result = self.llm.chat(
            prompt
        )

        return self._parse(
            result
        )

    # LLM 很爱把 JSON 包在 ```json 围栏里，
    # 也可能在前后再带一段解释文字。
    # 直接 json.loads 会抛异常，
    # 一个 case 崩掉就把整轮 Evaluation 拖死，
    # 所以这里必须兜底。
    @staticmethod
    def _parse(
        raw: str,
    ) -> dict:

        text = (raw or "").strip()

        # 去掉 Markdown 代码围栏
        if text.startswith("```"):

            text = re.sub(
                r"^```[a-zA-Z]*\s*",
                "",
                text,
            )

            text = re.sub(
                r"\s*```$",
                "",
                text,
            )

        try:
            return json.loads(text)

        except json.JSONDecodeError:
            pass

        # 退一步：从文本里抠出第一个 {...}
        match = re.search(
            r"\{.*\}",
            text,
            re.DOTALL,
        )

        if match:

            try:
                return json.loads(
                    match.group(0)
                )

            except json.JSONDecodeError:
                pass

        # 彻底解析不出来时，
        # 给 0 分并把原始输出留在 reason 里，
        # 方便事后排查是 Prompt 问题还是模型问题。
        return {
            "answer_relevance": 0.0,
            "faithfulness": 0.0,
            "correctness": 0.0,
            "reason": (
                "无法解析 LLM Judge 输出："
                f"{raw!r}"
            ),
        }
