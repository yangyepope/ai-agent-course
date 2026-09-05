import re

from app.chunking.base import (
    BaseChunker,
    Chunk,
)


class RecursiveChunker(BaseChunker):

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

        self.separators = [
            "\n\n",
            "\n",
            "。",
            "！",
            "？",
            ".",
            "!",
            "?",
            " ",
            "",
        ]

    def split(
        self,
        text: str,
        metadata: dict | None = None,
    ) -> list[Chunk]:

        metadata = metadata or {}

        raw_chunks = self._recursive_split(
            text
        )

        chunks = []

        for index, content in enumerate(
            raw_chunks
        ):

            content = content.strip()

            if not content:
                continue

            chunks.append(
                Chunk(
                    chunk_id=(
                        f"{metadata.get('source', 'document')}"
                        f"-{index}"
                    ),
                    content=content,
                    metadata={
                        **metadata,
                        "chunk_index": index,
                    },
                )
            )

        return chunks

    def _recursive_split(
        self,
        text: str,
    ) -> list[str]:

        if len(text) <= self.chunk_size:
            return [text]

        separator = self._find_separator(
            text
        )

        if separator == "":
            return self._split_by_size(
                text
            )

        parts = text.split(
            separator
        )

        chunks = []

        current = ""

        for part in parts:

            if not part:
                continue

            candidate = (
                current
                + separator
                + part
                if current
                else part
            )

            if len(candidate) <= self.chunk_size:

                current = candidate

            else:

                if current:
                    chunks.append(
                        current
                    )

                if len(part) <= self.chunk_size:

                    current = part

                else:

                    chunks.extend(
                        self._recursive_split(
                            part
                        )
                    )

                    current = ""

        if current:
            chunks.append(current)

        return self._apply_overlap(
            chunks
        )

    def _find_separator(
        self,
        text: str,
    ) -> str:

        for separator in self.separators:

            if separator and separator in text:
                return separator

        return ""

    def _split_by_size(
        self,
        text: str,
    ) -> list[str]:

        chunks = []

        start = 0

        while start < len(text):

            end = min(
                start + self.chunk_size,
                len(text),
            )

            chunks.append(
                text[start:end]
            )

            start = end

        return chunks

    def _apply_overlap(
        self,
        chunks: list[str],
    ) -> list[str]:

        if self.overlap == 0:
            return chunks

        result = []

        for index, chunk in enumerate(
            chunks
        ):

            if index == 0:

                result.append(chunk)

                continue

            previous = chunks[
                index - 1
            ]

            overlap_text = previous[
                -self.overlap:
            ]

            result.append(
                overlap_text + chunk
            )

        return result
