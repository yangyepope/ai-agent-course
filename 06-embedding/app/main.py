import os

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings


load_dotenv()
from pydantic import SecretStr

# 统一用 os.environ 显式读取：缺失时立即抛 KeyError（附变量名），
# 避免 None 悄悄传入模型导致难以定位的运行时错误
embeddings = OpenAIEmbeddings(
    model=os.environ["LLM_EMBEDDING_MODEL"],
    api_key=SecretStr(os.environ["LLM_API_KEY"]),
    base_url=os.environ["LLM_BASE_URL"],
    # 非 OpenAI 服务商（阿里云百炼）只接受原始字符串数组，
    # 关闭 token 化检查可绕过 token id 数组不兼容问题
    check_embedding_ctx_length=False,
)



vector = embeddings.embed_query(
    "我喜欢吃苹果"
)


print(
    type(vector)
)

print(
    len(vector)
)

print(
    vector[:10]
)



# documents = [
#     "Java 是一种面向对象的编程语言。",
#     "Spring Boot 可以快速开发 Java Web 应用。",
#     "MySQL 是一种关系型数据库。",
#     "Redis 是一种内存数据库。",
#     "Python 广泛应用于人工智能领域。",
# ]


# vectors = embeddings.embed_documents(
#     documents
# )


# for document, vector in zip(
#     documents,
#     vectors,
# ):

#     print(
#         document
#     )

#     print(
#         len(vector)
#     )

#     print(
#         vector[:5]
#     )

#     print("---")

try:
    import numpy as np  # type: ignore[import-not-found]
except ImportError as exc:
    raise RuntimeError(
        "缺少依赖 numpy，请在当前 Python 环境中安装：pip install numpy"
    ) from exc


def cosine_similarity(
    a: list[float],
    b: list[float],
) -> float:

    a = np.array(a)
    b = np.array(b)

    return float(
        np.dot(a, b)
        / (
            np.linalg.norm(a)
            * np.linalg.norm(b)
        )
    )


documents = [
    "Java 是一种面向对象的编程语言。",
    "Spring Boot 可以快速开发 Java Web 应用。",
    "MySQL 是一种关系型数据库。",
    "Redis 是一种内存数据库。",
    "Python 广泛应用于人工智能领域。",
]


document_vectors = embeddings.embed_documents(
    documents
)


query = "Spring Boot 怎么连接数据库？"


query_vector = embeddings.embed_query(
    query
)


results = []


# 代码等价于：
""" 
for i in range(len(documents)):
    document = documents[i]
    vector = document_vectors[i]
    # 每轮循环体

"""

for document, vector in zip(
    documents,
    document_vectors,
):
    


    score = cosine_similarity(
        query_vector,
        vector,
    )

    results.append(
        (
            score,
            document,
        )
    )


results.sort(
    reverse=True
)


for score, document in results:

    print(
        f"{score:.4f} - {document}"
    )