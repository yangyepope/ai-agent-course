from dataclasses import dataclass


@dataclass
class DocumentChunk:
    id: str
    content: str
    source: str
    page: int
    category: str
    tenant_id: str


"""
后续可能涉及
department_id
user_id
permission
document_id
knowledge_base_id

"""
