
'''
定义模型
'''


from dataclasses import dataclass


@dataclass
class Document:
    id: str
    content: str
    source: str
    page: int
    category: str