# 这个一定要理解

方法	      输入	          输出	              核心目的
Rewrite	     Query	         Query	            优化搜索表达
Multi-Query	 Query	         多个 Query	         扩大召回
HyDE	     Query	         假设文档	          改善语义匹配

可以记成：

Rewrite
=
换一种更适合搜索的说法

Multi-Query
=
从多个角度搜索

HyDE
=
先想象一个相关文档，再拿它搜索


# 三种方式的 Pipeline
Rewrite
User Query
   ↓
Rewrite
   ↓
Search Query
   ↓
Embedding
   ↓
Vector Search
Multi-Query
User Query
   ↓
┌────┬────┬────┬────┐
Q1   Q2   Q3   Q4   Q5
│    │    │    │    │
▼    ▼    ▼    ▼    ▼
Retrieval × 5
   ↓
Merge
   ↓
Dedup
HyDE
User Query
    ↓
LLM
    ↓
Hypothetical Document
    ↓
Embedding
    ↓
Vector Search
