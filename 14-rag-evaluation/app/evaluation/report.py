class EvaluationReport:

    def __init__(
        self,
        dataset_size: int,
    ):
        self.dataset_size = dataset_size
        self.metrics = {}

    def add(
        self,
        name: str,
        value: float,
    ):

        self.metrics[name] = value

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

        print()

        print(
            "Retrieval"
        )

        print(
            "-" * 60
        )

        for name, value in (
            self.metrics.items()
        ):

            print(
                f"{name:<25}"
                f": {value:.4f}"
            )

        print()

        print(
            "=" * 60
        )
