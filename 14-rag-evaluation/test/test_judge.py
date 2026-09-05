from app.evaluation.judge import LLMJudge


class StubLLM:

    def __init__(
        self,
        response: str,
    ):
        self.response = response

    def chat(
        self,
        prompt: str,
    ) -> str:

        return self.response


def 打分(response: str) -> dict:

    judge = LLMJudge(
        llm=StubLLM(response)
    )

    return judge.evaluate(
        question="Q",
        context="C",
        answer="A",
        ground_truth="G",
    )


def test_纯_json():

    result = 打分(
        '{"answer_relevance": 1.0,'
        ' "faithfulness": 0.8,'
        ' "correctness": 0.9,'
        ' "reason": "ok"}'
    )

    assert result["faithfulness"] == 0.8

    assert result["correctness"] == 0.9


def test_带_markdown_围栏():

    result = 打分(
        "```json\n"
        '{"answer_relevance": 1.0,'
        ' "faithfulness": 0.5,'
        ' "correctness": 0.5,'
        ' "reason": "ok"}\n'
        "```"
    )

    assert result["faithfulness"] == 0.5


def test_前后带解释文字():

    result = 打分(
        "好的，我的评价如下：\n"
        '{"answer_relevance": 0.2,'
        ' "faithfulness": 0.3,'
        ' "correctness": 0.4,'
        ' "reason": "ok"}\n'
        "希望有帮助。"
    )

    assert result["correctness"] == 0.4


def test_完全解析不出来时不崩():

    result = 打分(
        "我拒绝回答"
    )

    assert result["faithfulness"] == 0.0

    assert "无法解析" in result["reason"]
