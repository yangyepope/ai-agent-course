'''
加载文档

'''


import json
from pathlib import Path

from app.models import Document


DATA_FILE = Path("data/documents.json")


def load_documents() -> list[Document]:
    with DATA_FILE.open(
        "r",
        encoding="utf-8",
    ) as f:
        data = json.load(f)

    return [
        Document(
            id=item["id"],
            content=item["content"],
            source=item["source"],
            page=item["page"],
            category=item["category"],
        )
        for item in data
    ]