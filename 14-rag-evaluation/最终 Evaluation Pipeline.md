                evaluation_dataset.json
                          │
                          ▼
                 EvaluationDataset
                          │
                          ▼
                    RAGEvaluator
                          │
                          ▼
                  RAGService.retrieve()
                          │
                          ▼
                  Retrieved Documents
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
       Retrieval Metrics        Context Construction
              │                       │
      ┌───────┼───────┐               ▼
      ▼       ▼       ▼             LLM
    Recall Precision MRR             │
            NDCG                     ▼
                                   Answer
                                     │
                                     ▼
                                  LLM Judge
                                     │
                         ┌───────────┼───────────┐
                         ▼           ▼           ▼
                      Relevance Faithfulness Correctness
                         │           │           │
                         └───────────┴───────────┘
                                     │
                                     ▼
                              Evaluation Report
