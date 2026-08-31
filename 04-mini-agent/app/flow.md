                User
                  │
                  ▼
             ┌─────────┐
             │   LLM   │
             └────┬────┘
                  │
           Tool Calling?
             │        │
            No       Yes
             │        │
             ▼        ▼
          Answer    Tool Map
                        │
                        ▼
                 ┌────────────┐
                 │  Python    │
                 │   Tool     │
                 └─────┬──────┘
                       │
                       ▼
                  Tool Result
                       │
                       ▼
                    Message
                       │
                       └──────→ LLM