# ES 在这个项目里到底是什么

> 配套阅读：[简易流程图.md](简易流程图.md)（一张图看完整流程）、[学习心得.md](学习心得.md)（逐文件拆解）、[问答.md](问答.md)（text vs dense_vector 原理）
>
> 本文只回答四个问题：
> ```
> ① ES 具体是做什么的？      ──► 一、二 章
> ② 数据由谁写进去？         ──► 三、四 章
> ③ 写进去给谁查询？         ──► 三、五 章
> ④ 具体是怎么查询的？       ──► 五、六 章
> ```

---

# 一、首先：ES 不是一个 Python 库，是一个独立进程

这是最容易搞混的地方。`pip install elasticsearch` 装的**不是** ES 本身，
而是**一个 HTTP 客户端**。ES 本体是一台独立跑着的服务（Java 写的，监听 9200）。

```
   你的 Python 项目                             Elasticsearch 服务
（12-elasticsearch-rag/app/）                  （独立进程，端口 9200）
          │                                              │
          │  ┌────────────────────────────────────┐      │
          └──┤        HTTP + JSON                 ├─────►│
             └────────────────────────────────────┘      │
                                                         ├──► 内存（HNSW 图/缓存）
                                                         └──► 磁盘（持久化）
```

所以 `elasticsearch` 这个包里的每个方法，本质都是**一次 HTTP 请求**：

```
Python 写法                              实际发出的 HTTP 请求
─────────────────────────────────────────────────────────────────────────
client.indices.exists(index=...)   ──►  HEAD   /rag_chunks
client.indices.create(...)         ──►  PUT    /rag_chunks
client.index(index=..., id=..., …) ──►  PUT    /rag_chunks/_doc/chunk-001
client.indices.refresh(...)        ──►  POST   /rag_chunks/_refresh
client.search(index=..., …)        ──►  POST   /rag_chunks/_search
client.ping()                      ──►  HEAD   /
```

**推论**：凡是 Python 能做的，curl 都能做，反之也一样。
这就是为什么 [init_index.py](app/init_index.py) 末尾留了一行 curl 注释 ——
它和 `client.indices.get()` 是**同一件事**：

```
python -m app.init_index                                   建索引
        ↕  验证的是同一个东西
curl -s --noproxy '*' http://127.0.0.1:9200/rag_chunks     看索引
```

ES 起不起来、跑在哪、怎么装，跟这个项目的 Python 代码**完全无关**
（见仓库根目录的 [Elasticsearch部署与使用.md](../Elasticsearch部署与使用.md)）。
项目代码只知道一个地址：`http://127.0.0.1:9200`，而且只写在
[elasticsearch_client.py](app/elasticsearch_client.py) 一个地方。

# 二、ES 在这个项目里承担哪几件事

第 8 课和第 11 课，这些活全是 Python 进程自己在内存里干的。
这一课把它们**整体搬到进程外，做成一个服务**：

```
                        Elasticsearch 承担的 4 件事
                                    │
    ┌───────────────┬───────────────┼───────────────┬───────────────┐
    ↓               ↓               ↓               ↓               ↓
 ① 存储          ② 倒排索引       ③ 向量索引       ④ 过滤 + 融合 + 排序
    │               │               │               │
 落磁盘          分词建倒排表      建 HNSW 图      filter / RRF / size 截断
    │               │               │               │
 进程重启         BM25 打分        kNN 近似最近邻    先隔离再排序
 数据还在            │               │               │
    │               ↓               ↓               ↓
    │            content         embedding      tenant_id 等 keyword
    │           (type: text)   (dense_vector)
    ↓
 分片 + 副本 ──► 可水平扩展
```

对比一下这一课解决了什么：

```
第 8/11 课（Python 进程内）                第 12 课（ES 服务）
─────────────────────────────────────────────────────────────────
向量在 numpy 数组里        ──►  向量在 ES 索引里（落盘）
进程退出 = 数据全丢        ──►  进程退出 = 数据还在
BM25 自己实现/调库         ──►  ES 原生 BM25
相似度自己 for 循环算       ──►  ES 的 HNSW 近似搜索
RRF 拉回 Python 自己算      ──►  ES 内部 retriever 融合
没有多租户概念             ──►  term filter 一行搞定
单机、单进程               ──►  分片 + 副本 + 集群
```

# 三、数据由谁写进去、给谁查询（全景）

这个项目里，**写方和读方是两个完全不同的东西**：

```
                          ┌──────────────────────────────┐
                          │   Elasticsearch  :9200       │
                          │   ┌──────────────────────┐   │
                          │   │  索引 rag_chunks     │   │
     ①写 ─────────────────┼──►│  ┌────────────────┐  │   │
                          │   │  │ chunk-001      │  │   │
                          │   │  │ chunk-002      │  │◄──┼───────── ②读
                          │   │  │ chunk-003      │  │   │
                          │   │  │ chunk-004      │  │   │
                          │   │  └────────────────┘  │   │
                          │   └──────────────────────┘   │
                          └──────────────────────────────┘
                                     ↑            ↑
        ┌────────────────────────────┘            └────────────────────────────┐
        │                                                                      │
【① 写方 = Writer】                                          【② 读方 = Reader】
                                                    
data/documents.json                                  用户 / 前端 / 上层 Agent
        │                                                          │
        ↓                                                          ↓
python -m app.index_documents                        POST /api/retrieval/search
（离线脚本，人手动跑一次）                              （在线服务，一直在跑）
        │                                                          │
        ↓                                                          ↓
DocumentService                                              api.py: search()
  ├─ load_documents()                                              │
  ├─ EmbeddingService.embed_batch()                                ↓
  └─ client.index() × 4                                     SearchService
        │                                                    .hybrid_search()
        ↓                                                          │
  PUT /rag_chunks/_doc/{id}                                        ├─ embed(query)
        │                                                          ↓
        └──────────────► ES ◄───────────────────────────  POST /rag_chunks/_search
                          │
                          └──► BM25 + kNN + RRF ──► top_k ──► 整理 ──► HTTP 响应
```

一张表说清三个角色：

| 角色 | 具体是谁 | 干什么 | 什么时候跑 | 频率 |
|---|---|---|---|---|
| **建表方** | `init_index.py` | 定义 mapping，创建索引 | 上线前 | **1 次** |
| **写方** | `index_documents.py` | 语料 → 向量 → 写 ES | 有新文档时 | **少**（离线批量） |
| **读方** | `api.py` + `search_service.py` | 收 HTTP 请求 → 查 ES → 返回 | 服务常驻 | **多**（每个请求） |

**"写少读多"** 就是为什么写入是脚本、查询是服务：

```
写入 ──► 4 条文档要跑 Embedding 模型 ──► 慢、CPU/GPU 密集 ──► 适合离线批量
读取 ──► 1 条 query 跑 Embedding ──► 快 ──► 适合在线实时
```

> 注意：现在项目里**没有"通过 API 写入"的入口**，也没有删除/更新接口。
> 想更新数据只能重跑 `index_documents.py`。因为写入用了
> `id=document["id"]`，重跑是**覆盖**而不是产生重复文档（幂等）。
> 真实项目里这一步会变成 `/api/ingest` 接口或 MQ 消费者。

# 四、写入时，ES 内部到底发生了什么

拿 `chunk-002` 走一遍全程：

```
data/documents.json
{
  "id": "chunk-002",
  "content": "Redis 的 maxmemory-policy 用于控制 Redis 内存达到 maxmemory 限制后如何淘汰数据。",
  "source": "redis-guide.pdf",
  "page": 15,
  "category": "redis",
  "tenant_id": "tenant-001"
}
        │
        ↓  DocumentService.load_documents()
   Python dict
        │
        ↓  EmbeddingService.embed_batch()  ← content 变成向量
   embedding = [0.018, -0.087, 0.217, ..., 0.041]   （512 个数）
        │
        ↓  拼 body
   {chunk_id, content, source, page, category, tenant_id, embedding}
        │
        ↓  client.index(index="rag_chunks", id="chunk-002", document=body)
   PUT http://127.0.0.1:9200/rag_chunks/_doc/chunk-002
   Content-Type: application/json
   { ...body... }
        │
        ↓  ═══════ 边界：这里之后是 ES 内部的事 ═══════
        │
   ES 收到，照 mapping 处理每个字段
        │
   ┌────┴────────────────┬──────────────────┬─────────────────┐
   ↓                     ↓                  ↓                 ↓
content (text)     embedding          tenant_id 等        _source
   │              (dense_vector)       (keyword)             │
   ↓                     ↓                  ↓                ↓
分词器切词          插入 HNSW 图        整串存进            原始 JSON
   │                     │              doc_values          原样留存
   ↓                     ↓                  ↓                │
写入倒排表           建立邻居连接         供 filter 用          └──► 查询时
                                                                   返回给你
```

**倒排表**长这样（ES 为 `content` 建的，BM25 就靠它）：

```
    词           →  出现在哪些文档（及位置/词频）
  ─────────────────────────────────────────────
    Redis        →  chunk-001, chunk-002, chunk-003
    maxmemory    →  chunk-002
    policy       →  chunk-002
    内存          →  chunk-001, chunk-002, chunk-004
    淘汰          →  chunk-002
    数据          →  chunk-002, chunk-003
    Cluster      →  chunk-003
    G1           →  chunk-004
    ...
```

**HNSW 图**长这样（ES 为 `embedding` 建的，kNN 就靠它）：

```
       chunk-001 ●───────● chunk-002        ← Redis 三兄弟向量挨得近
            │  ╲       ╱   │
            │    ╲   ╱     │
            │      ●       │  chunk-003
            │              │
            └──── ● ───────┘
              chunk-004                     ← Java G1，离得远
```

`indices.refresh()` 的作用就在这个边界上：

```
client.index() 返回成功
        │
        └──► 数据进了 ES，但还在内存 buffer 里
                    │
                    ├──► 不 refresh ──► 搜不到（要等默认 1 秒）
                    └──► refresh    ──► 生成新 segment ──► 立刻可搜  ✓
```

# 五、查询时，ES 内部到底发生了什么

拿真实 query `"Redis内存满了怎么淘汰"` 走一遍。
**注意这个 query 里根本没有 "maxmemory-policy" 这几个字** ——
这正好能看出为什么要混合检索。

```
用户 / 前端
        │
        ↓  POST /api/retrieval/search?query=Redis内存满了怎么淘汰
        │       &tenant_id=tenant-001&top_k=3
   api.py: search()
        │
        ↓  search_service.hybrid_search()
        │
        ├──► embedding_service.embed("Redis内存满了怎么淘汰")
        │           └──► query_vector = [0.013, -0.092, 0.221, ..., 0.045]
        │
        ↓  client.search(index="rag_chunks", retriever={rrf: [...]}, size=3)
   POST http://127.0.0.1:9200/rag_chunks/_search
        │
        ↓  ═══════ 边界：这里之后是 ES 内部的事 ═══════
        │
   ES 解析 retriever，并行跑两路
        │
   ┌────┴──────────────────────────────┬─────────────────────────────────┐
   ↓                                   ↓                                 │
【路 A：standard / BM25】          【路 B：knn】                          │
   │                                   │                                 │
   ↓ ① filter 先砍                     ↓ ① filter 先砍（pre-filter）      │
term tenant_id = tenant-001        term tenant_id = tenant-001           │
   │  └──► 只剩本租户的文档            │  └──► 只剩本租户的向量            │
   ↓ ② query 分词                      ↓ ② HNSW 图上跳跃                  │
"Redis内存满了怎么淘汰"                 从入口点出发，一路走向              │
   └──► Redis / 内存 / 满 /            离 query_vector 更近的邻居          │
        了 / 怎么 / 淘汰                │                                 │
   ↓ ③ 查倒排表                        ↓ ③ 捞 num_candidates=100 个候选    │
Redis → 001,002,003                    （本例只有 4 条，全进候选）         │
内存  → 001,002,004                    │                                 │
淘汰  → 002                            ↓ ④ 算 cosine 相似度               │
   ↓ ④ BM25 打分                       chunk-002: 0.89                   │
（词频 TF / 逆文档频率 IDF /            chunk-003: 0.71                   │
  字段长度归一化）                      chunk-001: 0.68                   │
   │  "淘汰" 只在 002 出现              chunk-004: 0.12                   │
   │   → IDF 高 → 002 得分最高          │                                 │
   ↓                                   ↓ ⑤ 取 k=20                       │
榜单 A（按 BM25 分）                   榜单 B（按 cosine）                 │
  ① chunk-002  12.7                     ① chunk-002                      │
  ② chunk-001   6.3                     ② chunk-003                      │
  ③ chunk-004   4.1                     ③ chunk-001                      │
   │                                   │                                 │
   └───────────────┬───────────────────┘                                 │
                   ↓                                                     │
            【RRF 融合】 ◄───────────────────────────────────────────────┘
       rank_window_size=50  各取前 50 名参与
       rank_constant=60
                   │
                   ↓  score = Σ 1/(60 + rank)
       chunk-002: 1/61 + 1/61 = 0.0328   ← 两个榜单都第 1 ✓✓
       chunk-001: 1/62 + 1/63 = 0.0320   ← 一个第 2 一个第 3
       chunk-003: 1/63 + 1/62 = 0.0320   ← 一个第 3（BM25 没进）+ 第 2
       chunk-004: 1/63        = 0.0159   ← 只有 BM25 命中（"内存"）
                   │
                   ↓  size=3 截断
       [chunk-002, chunk-001, chunk-003]
                   │
                   ↓  ═══════ 边界：回到 Python ═══════
   response["hits"]["hits"]
   [ {_index, _id, _score, _source:{chunk_id, content, source, page, ...}}, ... ]
                   │
                   ↓  api.py 整理（丢掉 _index/_shard 等内部字段）
   { "query": "Redis内存满了怎么淘汰",
     "results": [
       {"id":"chunk-002", "score":0.0328, "content":"Redis 的 maxmemory-policy…",
        "source":"redis-guide.pdf", "page":15},
       ... ] }
                   │
                   ↓
              HTTP 响应 ──► 用户
```

**这个例子说明的问题**：

```
query = "Redis内存满了怎么淘汰"（用户的自然说法）
文档   = "maxmemory-policy 用于控制…如何淘汰数据"（文档的专业说法）
        │
        ├──► 纯 BM25 ──► 只靠 "Redis"/"内存"/"淘汰" 三个词勉强命中
        │                  └──► 如果用户说"缓存满了" ──► 一个词都不沾 ──► ✗ 搜不到
        │
        ├──► 纯 kNN  ──► 语义上强命中 ✓
        │                  └──► 但如果用户直接搜 "maxmemory-policy" 这种专有名词
        │                       向量反而不敏感 ──► 可能被别的 Redis 文档挤掉
        │
        └──► Hybrid  ──► 两种说法都能搜到  ✓✓
```

# 六、写方和读方唯一的耦合点

写方和读方是两个不同的进程、不同的时间跑的，它们之间**没有任何直接调用**。
唯一的契约是 [index_manager.py](app/index_manager.py)：

```
                 index_manager.py
        ┌────────────────────────────────┐
        │  INDEX_NAME = "rag_chunks"     │  ← 索引名
        │  mappings = { ... }            │  ← 字段名 + 类型
        └───────────┬────────────────────┘
                    │
        ┌───────────┴───────────┐
        ↓                       ↓
  document_service.py     search_service.py
  （写方 import 它）        （读方 import 它）
        │                       │
        ↓                       ↓
  按 mapping 写字段        按 mapping 查字段
        │                       │
        └───────► 对齐 ◄────────┘
```

**不对齐时，问题往往不在写入阶段暴露，而是等到查询才发现**：

```
不对齐的情形                            写入时              查询时
──────────────────────────────────────────────────────────────────────────
写方写 "content" / 读方查 "text"        ✓ 成功       ✗ 命中 0，且无报错  ⚠️ 最难查
写方 512 维 / mapping 声明 768 维        ✗ 直接报错    —                （这个反而好）
没建索引就写（dynamic mapping 猜类型）    ✓ 静默成功    ✗ 明确报错：
   └──► embedding 被猜成 float                        [knn] queries are only
                                                      supported on
                                                      [dense_vector] fields
tenant_id 定成 text / 查询用 term        ✓ 成功       ✗ 匹配不上，无报错
写方存 chunk_id / api.py 读 chunk_id     —            ✗ KeyError（这个会崩）
```

真正难查的是**「命中 0 但不报错」**那几种：字段名写错、keyword 定成了 text。
类型不匹配（float vs dense_vector）反而会给你一句清楚的错误。

所以那三个 keyword 字段和 `dims: 512`，本质上是**写方和读方之间的接口定义**，
不是随便写的配置。

# 七、时间线：谁在什么时候动 ES

```
时间 ──────────────────────────────────────────────────────────────────►

T0   ES 服务启动
     （docker / systemd，独立于本项目，见 Elasticsearch部署与使用.md）
              │
T1   python -m app.test                       ──► 不碰 ES，只测模型
              │
T2   python -m app.init_index                 ──► 建索引        【1 次】
              │                                    HEAD/PUT /rag_chunks
              │
T3   python -m app.index_documents            ──► 灌数据        【少】
              │                                    PUT /_doc/× 4
              │                                    POST /_refresh
              │
T4   uvicorn app.main:app                     ──► 起服务，常驻
              │                                    加载模型 1 次
              │                                    建 ES 连接 1 次
              │
T5   POST /api/retrieval/search               ──► 查询          【多】
T6   POST /api/retrieval/search                    POST /_search
T7   POST /api/retrieval/search                    …无限次
     …
```

```
T1、T2、T3  ──► 一次性、离线、人手动跑   ──► 脚本形态（有 main()）
T4 之后      ──► 常驻、在线、被动响应    ──► 服务形态（uvicorn）
        │
        └──► 这就是 [学习心得.md](学习心得.md) 里"能力层 / 一次性脚本 / 在线服务"三分类的由来
```

