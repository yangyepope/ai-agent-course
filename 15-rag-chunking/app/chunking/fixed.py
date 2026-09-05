from app.chunking.base import (
    BaseChunker,
    Chunk,
)


class FixedChunker(BaseChunker):

    def __init__(
        self,
        chunk_size: int = 500,
        overlap: int = 50,
    ):
        if chunk_size <= 0:
            raise ValueError(
                "chunk_size 必须大于 0"
            )

        if overlap < 0:
            raise ValueError(
                "overlap 不能小于 0"
            )

        if overlap >= chunk_size:
            raise ValueError(
                "overlap 必须小于 chunk_size"
            )

        self.chunk_size = chunk_size
        self.overlap = overlap

    def split(
        self,
        text: str,
        metadata: dict | None = None,
    ) -> list[Chunk]:

        metadata = metadata or {}

        chunks = []

        start = 0

        chunk_number = 0

        step = (
            self.chunk_size
            - self.overlap
        )

        while start < len(text):

            end = min(
                start + self.chunk_size,
                len(text),
            )

            content = text[
                start:end
            ].strip()

            if content:

                chunk_id = (
                    f"{metadata.get('source', 'document')}"
                    f"-{chunk_number}"
                )

                chunks.append(
                    Chunk(
                        chunk_id=chunk_id,
                        content=content,
                        metadata={
                            **metadata,
                            "chunk_index": chunk_number,
                        },
                        start_index=start,
                        end_index=end,
                    )
                )

                chunk_number += 1

            start += step

        return chunks
