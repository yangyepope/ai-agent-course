from sentence_transformers import SentenceTransformer


class EmbeddingService:

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-zh-v1.5",
    ):
        self.model = SentenceTransformer(
            model_name
        )

    def embed_documents(
        self,
        texts: list[str],
    ):
        return self.model.encode(
            texts,
            normalize_embeddings=True,
        )

    def embed_query(
        self,
        query: str,
    ):
        return self.model.encode(
            [query],
            normalize_embeddings=True,
        )[0]