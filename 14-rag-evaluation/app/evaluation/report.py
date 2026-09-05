class EvaluationReport:

    def __init__(
        self,
        dataset_size: int,
    ):
        self.dataset_size = dataset_size

        # {section: {name: value}}
        # 检索指标和生成指标是两类东西，
        # 混在一起打印会看不出问题出在哪一段。
        self.sections: dict[
            str,
            dict[str, float],
        ] = {}

    def add(
        self,
        name: str,
        value: float,
        section: str = "Retrieval",
    ):

        self.sections.setdefault(
            section,
            {},
        )[name] = value

    def print(self):

        print()

        print(
            "=" * 60
        )

        print(
            "RAG Evaluation Report"
        )

        print(
            "=" * 60
        )

        print(
            f"Dataset Size: "
            f"{self.dataset_size}"
        )

        for section, metrics in (
            self.sections.items()
        ):

            print()

            print(section)

            print(
                "-" * 60
            )

            for name, value in (
                metrics.items()
            ):

                print(
                    f"{name:<25}"
                    f": {value:.4f}"
                )

        print()

        print(
            "=" * 60
        )
