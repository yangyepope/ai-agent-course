你以后做企业级 RAG，基本都会看到这条链：

                    用户问题
                       │
                       ▼
                  Query Embedding
                       │
                       ▼
                 向量相似度搜索
                       │
              ┌────────┴────────┐
              ▼                 ▼
           文档 A              文档 B
              │                 │
              └────────┬────────┘
                       ▼
                  Relevant Docs
                       │
                       ▼
                Prompt + Context
                       │
                       ▼
                      LLM
                       │
                       ▼
                    最终答案


Embedding 则是：

用户问题
    ↓
Embedding
    ↓
向量

文档
    ↓
Embedding
    ↓
向量

比较两个向量
    ↓
语义相似度


在企业 RAG 里面常见：

OpenAI Embedding
Qwen Embedding
BGE
Jina Embeddings
Cohere Embedding

如果是国内/自部署场景，还经常看到：

BAAI/bge-m3
Qwen3-Embedding
