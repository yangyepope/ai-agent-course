"""
文件用途：Embedding 模型的"冒烟测试"脚本（12-elasticsearch-rag 课程用）。

做什么：
    1. 加载本地 Embedding 模型（BAAI/bge-small-zh-v1.5）；
    2. 打印模型输出的向量维度。

为什么需要它：
    本章要把文档向量写入 Elasticsearch，建索引（mapping）时必须
    提前声明向量字段的维度（dims），而维度由你选的 Embedding 模型决定
    （bge-small-zh-v1.5 输出 512 维）。跑一下这个脚本就能确认：
        - 模型能否正常下载/加载；
        - 输出维度是多少（后续建索引要用这个数字）。
"""

from sentence_transformers import SentenceTransformer

# 1. 加载 Embedding 模型
#    首次运行会自动从 HuggingFace 下载模型（约 100MB），之后走本地缓存
model = SentenceTransformer(
    "BAAI/bge-small-zh-v1.5"
)

# 2. 打印模型的输出向量维度
#    旧版 API 叫 get_sentence_embedding_dimension()，
#    sentence-transformers 5.x 起更名为 get_embedding_dimension()
print(model.get_embedding_dimension())
