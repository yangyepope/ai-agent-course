import re

from app.chunking.base import (
    BaseChunker,
    Chunk,
)


class MarkdownChunker(BaseChunker):

    HEADING_PATTERN = re.compile(
        r"^(#{1,6})\s+(.+)$"
    )

    def split(
        self,
        text: str,
        metadata: dict | None = None,
    ) -> list[Chunk]:

        metadata = metadata or {}

        lines = text.splitlines()

        chunks = []

        current_lines = []

        current_heading = None

        chunk_index = 0

        for line in lines:

            match = self.HEADING_PATTERN.match(
                line.strip()
            )

            if match:

                if current_lines:

                    content = "\n".join(
                        current_lines
                    ).strip()

                    if content:

                        chunks.append(
                            self._create_chunk(
                                content=content,
                                metadata=metadata,
                                heading=current_heading,
                                index=chunk_index,
                            )
                        )

                        chunk_index += 1

                level = len(
                    match.group(1)
                )

                heading = match.group(2)

                current_heading = {
                    "level": level,
                    "title": heading,
                }

                current_lines = [
                    line
                ]

            else:

                current_lines.append(line)

        if current_lines:

            content = "\n".join(
                current_lines
            ).strip()

            if content:

                chunks.append(
                    self._create_chunk(
                        content=content,
                        metadata=metadata,
                        heading=current_heading,
                        index=chunk_index,
                    )
                )

        return chunks

    def _create_chunk(
        self,
        content: str,
        metadata: dict,
        heading: dict | None,
        index: int,
    ) -> Chunk:

        chunk_metadata = {
            **metadata,
            "chunk_index": index,
        }

        if heading:

            chunk_metadata[
                "section"
            ] = heading["title"]

            chunk_metadata[
                "heading_level"
            ] = heading["level"]

        return Chunk(
            chunk_id=(
                f"{metadata.get('source', 'document')}"
                f"-{index}"
            ),
            content=content,
            metadata=chunk_metadata,
        )
