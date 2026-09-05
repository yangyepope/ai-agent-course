import json


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

        return json.loads(
            result
        )
