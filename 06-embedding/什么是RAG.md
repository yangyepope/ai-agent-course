                    User Query
                        │
                        ▼
                   Embedding
                        │
                        ▼
                   Query Vector
                        │
                        ▼
              Vector Similarity Search
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
       Spring Boot 文档        MySQL 文档
             │                     │
             └──────────┬──────────┘
                        ▼
                     Context
                        │
                        ▼
              ┌─────────────────┐
              │       LLM       │
              └────────┬────────┘
                       ▼
                    Answer



企业级 RAG 通常分成两个阶段：

                  RAG
                   │
          ┌────────┴────────┐
          │                 │
       离线阶段            在线阶段
       Indexing            Retrieval
          │                 │
          ▼                 ▼
       文档加载           用户 Query
          ↓                 ↓
       文本解析          Query Embedding
          ↓                 ↓
       Chunking           Vector Search
          ↓                 ↓
       Embedding          Top K
          ↓                 ↓
     Vector Database      Rerank
                            ↓
                         Context
                            ↓
                           LLM

你以后做企业级 RAG，一定要把这两个阶段分开理解。


今天你一定要记住这张图
                    RAG
                     │
                     ▼
              ┌─────────────┐
              │    Query    │
              └──────┬──────┘
                     │
                     ▼
                Embedding
                     │
                     ▼
                Query Vector
                     │
                     ▼
             Vector Database
                     │
                     ▼
              Similarity Search
                     │
                     ▼
                Top K Chunks
                     │
                     ▼
                 Context
                     │
                     ▼
             ┌──────────────┐
             │     LLM      │
             └──────┬───────┘
                    │
                    ▼
                  Answer