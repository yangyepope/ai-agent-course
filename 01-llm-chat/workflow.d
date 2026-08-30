                   POST /api/chat
                         │
                         ▼
                  ┌────────────┐
                  │  FastAPI   │
                  └─────┬──────┘
                        │
                        ▼
                    chat()
                        │
                        ▼
                ┌───────────────┐
                │   OpenAI SDK  │
                └───────┬───────┘
                        │
                   HTTP Request
                        │
                        ▼
                 ┌─────────────┐
                 │     LLM     │
                 └──────┬──────┘
                        │
                   Response
                        │
                        ▼
                    Python
                        │
                        ▼
                     JSON



API:
Python
 ↓
HTTP
 ↓
LLM


Context:
System
+
History
+
User
+
Context