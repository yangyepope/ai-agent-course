# Elasticsearch 本地部署与使用（12 章配套）

> 12-elasticsearch-rag 用 ES 做生产级检索后端：同一份文档里，
> `content` 字段走 **BM25 全文检索**，`embedding` 字段（512 维 dense_vector）走 **kNN 向量检索**。
> 本文记录本仓库 ES 的本地部署、客户端版本要求和实测踩坑。

---

## 1. 用 Docker 起单节点 ES

前提：机器已装 docker，且你的用户有 `sudo` 权限（本机 docker.sock 普通用户无权限）。

### 1.1 第一步：调内核参数（容器启动的硬性要求）

ES 的 mmap 需要较大的 `vm.max_map_count`，默认值太小会导致容器起不来：

```bash
sudo sysctl -w vm.max_map_count=262144
```

> 这只对本次生效；重启后失效就再执行一次，或写进 `/etc/sysctl.conf` 固化。

### 1.2 第二步：启动容器

```bash
sudo docker run -d --name es8 \
  -p 9200:9200 -p 9300:9300 \
  -e discovery.type=single-node \
  -e xpack.security.enabled=false \
  -e ES_JAVA_OPTS="-Xms512m -Xmx512m" \
  docker.elastic.co/elasticsearch/elasticsearch:8.15.5
```

各参数含义：

| 参数 | 作用 |
|---|---|
| `--name es8` | 容器名，后面 `docker stop/start/rm es8` 都用它 |
| `discovery.type=single-node` | 单节点模式，跳过集群发现，本地学习用 |
| `xpack.security.enabled=false` | **关掉安全认证**，代码用 `http://127.0.0.1:9200` 裸连，不用配账号密码 |
| `ES_JAVA_OPTS="-Xms512m -Xmx512m"` | 限制 JVM 堆内存，防止小内存机器（2~4G）启动时 OOM |
| 镜像 tag `8.15.5` | 12 章代码用了原生 RRF `retriever` 语法，**必须 ES 8.14+**（8.13 实测报 400 `Unknown key in [retriever]`）；8.15.x 是 8.x 里较新的稳定线 |

首次会自动拉镜像（约 1GB+，视网速等待）；第二次以后秒起。

### 1.3 第三步：验证

等 30~60 秒让 ES 完成初始化（容器刚起时 HTTP 还没就绪）：

```bash
curl -s --noproxy '*' http://127.0.0.1:9200
```

> ⚠️ 必须带 `--noproxy '*'`！本机 shell 设了 `http_proxy=http://127.0.0.1:7891`，
> 不带会走代理拿到空 502（详见第 4 节）。

正常返回 `200`，能看到 `"cluster_name": "docker-cluster"` 和 `"number": "8.15.5"`。

#### 为什么是 `--noproxy '*'`？

`--noproxy` 后面跟「不走代理的主机名单」，`*` 是通配符，表示**所有主机**——
即这次 curl 完全直连、不碰代理。原因：curl 会自动读环境变量
`http_proxy=http://127.0.0.1:7891`，把请求先交给 7891 代理转发，
而代理处理「指向本地自身」的请求会失败，返回一个**空响应体的 502**，
于是 `-s` 静默模式下屏幕上什么都看不到。

等价写法（三选一）：

```bash
curl --noproxy '*'        http://127.0.0.1:9200   # * = 全部直连（最常用）
curl --noproxy 127.0.0.1  http://127.0.0.1:9200   # 只对 127.0.0.1 直连
curl --proxy ""           http://127.0.0.1:9200   # 代理置空 = 禁用（-x "" 同义）
```

> 那环境变量 `NO_PROXY=127.*` 为什么没生效？curl 的 no_proxy 规则只认
> **域名后缀**（如 `example.com`）和 **CIDR**（如 `127.0.0.0/8`），
> **不认 `*` 通配符**，所以 `127.*` 匹配不上 `127.0.0.1`，请求仍然走了代理。
> Python 的 elasticsearch 客户端内部能正确处理 localhost 绕过，
> 只有你手动 `curl` 时需要加这个参数。

### 1.4 日常管理

```bash
sudo docker ps                # 看容器状态
sudo docker logs es8          # 看 ES 日志（起不来时先看这里）
sudo docker restart es8       # 重启
sudo docker stop es8          # 停止
sudo docker start es8         # 再次启动（数据还在容器里）
sudo docker rm es8            # 删除容器（数据一起删，慎用）
```

> 容器删了/重建后数据丢失——学习阶段无所谓；想持久化要挂 volume，课程不涉及。

### 1.5 RRF 融合检索需要试用许可（否则报 403）

docker 默认是 **Basic（免费）license**，而 12 章 `hybrid_search` 用的原生
**Reciprocal Rank Fusion (RRF) 属于付费功能**，Basic 下直接 403：

```
AuthorizationException: current license is non-compliant for
[Reciprocal Rank Fusion (RRF)]
```

本地学习开 **30 天全功能试用**即可（免费，随时可退回 Basic）：

```bash
curl -s --noproxy '*' -X POST \
  "http://127.0.0.1:9200/_license/start_trial?acknowledge=true"
```

返回 `"trial_was_started": true` 即生效，无需重启容器。到期后 RRF 会再次被拒；
如果不想依赖试用许可，就在代码里自己实现 RRF 融合（11 章的做法，纯免费）。

> 升级容器（`docker rm` + 重新 `docker run`）后索引和数据会丢，
> 记得重跑 `app/init_index.py` 建索引、`app/index_documents.py` 灌数据。

---

## 2. Python 客户端版本：必须 8.x，不能 9.x（本次最大坑）

**服务器（ES 8.15.5）和客户端（elasticsearch-py）必须同大版本。**

装了 `elasticsearch==9.5.0` 时，`es.ping()` 静默返回 `False`，`es.info()` 抛：

```
BadRequestError: media_type_header_exception
"Accept version must be either version 8 or 7, but found 9.
 Accept=application/vnd.elasticsearch+json; compatible-with=9"
```

原因：9.x 客户端发的 `Accept` 头声明 `compatible-with=9`，8.x 服务器只认 8/7，直接 400 拒绝。
`ping()` 内部把异常吞了，表现出来就是无声的 `False`——**特别容易误判成"网络不通"**。

### 正确姿势

```bash
cd /opt/ai-agent-course
uv add "elasticsearch>=8.13,<9"     # 装 8.x 客户端 + 写进 pyproject.toml + 更新 uv.lock
uv sync                             # 对齐环境
```

- 本仓库 `pyproject.toml` 已配好 `<9`，注释里写明了原因；
- 改完依赖后跑一次 `uv lock` 让 `uv.lock` 同步（此前 lock 还锁着 9.x 旧版时，`uv sync` 会把包拉回去）；
- 判断依据记牢：**服务器 8.x → 客户端 8.x；服务器 9.x 才能用客户端 9.x**。

---

## 3. 冒烟测试

装好且容器在跑时，验证连接：

```bash
cd /opt/ai-agent-course/12-elasticsearch-rag
../.venv/bin/python app/elasticsearch_client.py     # 应输出 True
```

```bash
../.venv/bin/python -c "
from elasticsearch import Elasticsearch
es = Elasticsearch('http://127.0.0.1:9200')
print('ping:', es.ping())
print('server:', es.info()['version']['number'])
"
```

预期：

```
ping: True
server: 8.15.5
```

---

## 4. 常见问题排查表

| 现象 | 原因 | 处理 |
|---|---|---|
| `ping()` 返回 `False`，`curl --noproxy '*' http://127.0.0.1:9200` 也连不上 | **ES 服务没启动**（9200 无监听） | `sudo docker ps` 看容器在不在；不在就按第 1 节启动，在就 `sudo docker logs es8` 看崩溃原因 |
| `ping()` 返回 `False`，但 `curl --noproxy '*'` 能通 | **客户端版本不匹配**（9.x 客户端连 8.x 服务器） | 按第 2 节降到 `>=8.13,<9` |
| `curl -s http://127.0.0.1:9200` 输出为空 / HTTP 502，但浏览器能访问 | curl 自动读 `http_proxy=127.0.0.1:7891` 把本地请求丢给代理；`NO_PROXY` 里的 `127.*` 通配写法 curl 不识别 | curl 一律加 `--noproxy '*'`，或 `env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY curl ...` |
| 容器反复重启 / 日志有 `max virtual memory areas vm.max_map_count` | 内核参数没调 | 先执行 `sudo sysctl -w vm.max_map_count=262144` 再启动容器 |
| 容器启动极慢 / 被 OOM kill | 默认 heap 1G+，小内存机器扛不住 | `docker run` 时带 `ES_JAVA_OPTS="-Xms512m -Xmx512m"`（第 1.2 节已带） |
| 端口被占：`docker run` 报 `port is already allocated` | 9200 被别的进程/旧容器占了 | `sudo lsof -i :9200` 找占用者；或 `sudo docker rm -f es8` 删掉旧容器重来 |
| `sudo docker ...` 报 `permission denied`（连 docker API 失败） | 当前用户不在 docker 组 | 用 `sudo docker`，别去改 docker 组 |
| 拉镜像超时 | 镜像约 1GB+，网络慢 | 重试（分层缓存，断点续传）；或换 `docker.elastic.co` 的其它 mirror |
| ES 版本 < 8.14 时搜索报 400 `parsing_exception: Unknown key for a START_OBJECT in [retriever]` | `retriever`（Retrievers API）语法在 8.14 起才可用，旧版不认顶层 `retriever` 参数 | 镜像升到 8.14+（本仓库用 8.15.5），见第 1 节 |
| 搜索报 403 `security_exception: current license is non-compliant for [Reciprocal Rank Fusion (RRF)]` | RRF 是付费 license 功能，docker 默认 Basic 许可不含 | 开 30 天试用：`curl -s --noproxy '*' -X POST "http://127.0.0.1:9200/_license/start_trial?acknowledge=true"`，见第 1.5 节 |

---

## 5. 与 12 章代码的关系

本章索引 `rag_chunks` 的 mapping 要点（见 `app/index_manager.py`）：

```python
mappings = {
    "properties": {
        "content":   {"type": "text"},                            # → BM25 全文检索
        "embedding": {                                            # → kNN 向量检索
            "type": "dense_vector",
            "dims": 512,                                          # 与 bge-small-zh-v1.5 输出维度一致
            "index": True,
            "similarity": "cosine",
        },
        # 其余字段：chunk_id / source / page / category / tenant_id → keyword / integer
    }
}
```

- `dims: 512` 来自 Embedding 模型输出维度，可跑 `app/test.py` 确认；
- 一条文档同时被 `content`（词法）和 `embedding`（语义）两套索引覆盖，
  后续做混合检索（hybrid search）时就是拿这两路结果做 RRF 融合。
