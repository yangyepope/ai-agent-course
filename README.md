# ai-agent-course

AI Agent 课程练习项目。

| 目录 | 说明 |
|---|---|
| `01-llm-chat` | FastAPI + OpenAI 兼容接口的最小对话服务 |
| `02-langchain-basic` | LangChain 基础：invoke / Prompt / OutputParser |
| `03-langchain-tool` | `@tool` 装饰器与工具对象的属性 |
| `04-mini-agent` | 手写 Agent 循环（`while` + `tool_map`），不依赖框架 |
| `05-langgraph-basic` | LangGraph：StateGraph / 条件路由 / add_messages |
| `06-embedding` | Embedding 与向量相似度 |
| `07-vector-db` | 向量数据库（FAISS） |
| `08-mini-rag` | 从 0 手写 Mini RAG |
| `09-document-chunking` | 文档切分策略（PDF 加载 + 各类 splitter） |
| `10-retriever-deeplearning` | Retriever 深入：召回质量、元数据过滤、权限 |
| `11-hybrid-search` | 混合检索：BM25 + 向量 + RRF 融合 + CrossEncoder 精排 |
| `main.py` | PyCharm 生成的模板文件，与课程无关 |

> 📌 [真实项目待补清单.md](真实项目待补清单.md) —— 从「课程练习」到「能上线的系统」还差什么：
> 评估体系、路线顺序修正、生产化能力清单，以及本仓库实跑中暴露的真实问题。

---

## 1. 环境搭建

Python **3.13**。**全部 11 章共用仓库根目录的一个 `.venv`**，依赖清单只有一份：
根目录的 `requirements.txt`。

> 早期各章各建了一个 `.venv`（11 个合计约 18GB，其中 09/10/11 各 5.3GB 是 GPU 版
> torch 拖进来的整套 `nvidia-*` CUDA 轮子）。现已统一成一个 CPU 版环境，约 1.4GB。
> 各章的 `requirements.txt` 保留为一行 `-r ../requirements.txt`，
> 所以 `pip install -r 09-document-chunking/requirements.txt` 这种老写法仍然可用。

### 方式 A：uv（推荐）

```bash
cd /opt/ai-agent-course

uv venv --python 3.13 .venv
VIRTUAL_ENV=.venv uv pip install -r requirements.txt --index-strategy unsafe-best-match
```

> `--index-strategy unsafe-best-match` 是必须的：`torch==2.13.0+cpu` 只存在于
> PyTorch 官方索引，而 uv 默认「命中第一个含该包的索引就停」，
> 会在 PyPI 上找不到 `+cpu` 版本而失败。pip 的默认行为不需要这个开关。

### 方式 B：标准 venv + pip

```bash
cd /opt/ai-agent-course

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> 若报 `No module named ensurepip`，需先装系统包：`sudo apt install python3-venv python3-pip`，或改用方式 A。

### 关于 torch

清单里锁的是 **CPU 版** `torch==2.13.0+cpu`，通过文件头部的
`--extra-index-url https://download.pytorch.org/whl/cpu` 获取。
本课程的 embedding / rerank 数据量在 CPU 上足够快（11 章全链路含 CrossEncoder
精排也是秒级）。若日后要换 GPU 版，把 `+cpu` 后缀去掉并删掉那行 `--extra-index-url` 即可，
届时会自动装回约 5GB 的 `nvidia-*` 依赖。

### 本地模型缓存

09~11 章用到两个 HuggingFace 模型，缓存在 `~/.cache/huggingface`（约 1.2GB）：

| 模型 | 用途 |
|---|---|
| `BAAI/bge-small-zh-v1.5` | 中文 Embedding（512 维） |
| `BAAI/bge-reranker-base` | CrossEncoder 精排 |

首次使用需要联网下载（HuggingFace 要走代理）。已缓存后可加 `HF_HUB_OFFLINE=1`
强制走本地缓存——这在「模型走代理、大模型端点要直连」两个需求冲突时很有用。

### WSL2 磁盘空间回收（删了文件但 Windows 空间没变）

在 WSL2 下，Linux 根分区是 Windows 上的一个虚拟磁盘文件：

```
C:\Users\<用户名>\AppData\Local\wsl\{<GUID>}\ext4.vhdx
```

**这个文件只会长大，不会自动缩小。** 所以合并虚拟环境省下的 17G，表现是：

| | 空间 |
|---|---|
| Linux 里 `df -h /` 的已用 | 31G → 14G（确实释放了） |
| Windows 上 ext4.vhdx 的体积 | 31.3G → 31.3G（**一点没变**） |

那 17G 只是变成了 vhdx **内部**的空闲块，Linux 写新文件会复用，
但 Windows 资源管理器里的可用空间不会涨。

#### 方案 A：开启稀疏磁盘（推荐，一劳永逸）

在 **Windows PowerShell（管理员）** 里执行（`Debian` 换成 `wsl -l -v` 里的发行版名）：

```powershell
wsl --shutdown
wsl --manage Debian --set-sparse true
```

转换过程会把当前空闲块还给 Windows，**而且以后每次删东西都会自动回收**，
不用再手动压缩。

再往 `C:\Users\<用户名>\.wslconfig` 补一段，让新建的磁盘也默认稀疏：

```ini
[experimental]
sparseVhd=true
```

> 稀疏磁盘唯一的代价是写入时有轻微开销，日常开发感觉不到。

#### 方案 B：只做一次性压缩

不想改配置就用 `diskpart`（Windows 家庭版也能用，不需要 Hyper-V）：

```powershell
wsl --shutdown
diskpart
```

进入 diskpart 后逐行输入：

```
select vdisk file="C:\Users\<用户名>\AppData\Local\wsl\{<GUID>}\ext4.vhdx"
attach vdisk readonly
compact vdisk
detach vdisk
exit
```

缺点是治标不治本——下次再删大文件还得重来一遍。

#### 顺带：清理僵尸 swap 文件

WSL 异常退出会在 Temp 里留下 swap 虚拟盘，每个 1~2G：

```
C:\Users\<用户名>\AppData\Local\Temp\<GUID>\swap.vhdx
```

`wsl --shutdown` 之后，除当前会话正在用的那个之外都可以直接删掉。

#### 排查命令

```bash
# Linux 侧实际占用
df -h /
du -sh /opt/ai-agent-course/.venv

# 从 WSL 里查看 Windows 上 vhdx 的真实体积
find /mnt/c -maxdepth 8 -iname 'ext4.vhdx' -printf '%s\t%p\n' 2>/dev/null \
  | awk -F'\t' '{printf "%.1f GB\t%s\n", $1/1073741824, $2}'

# 发行版名（方案 A 要用）
/mnt/c/Windows/System32/wsl.exe -l -v
```

> 两个 `df` 数字对不上时，先看 vhdx 体积——它才是 Windows 真正在意的那个数。

---

## 2. 配置

`01-llm-chat/.env`（已存在，不要提交到仓库）：

```dotenv
LLM_API_KEY=<你的 API Key>
LLM_BASE_URL=<OpenAI 兼容接口地址，例如阿里云百炼 compatible-mode>
LLM_MODEL=<模型名，例如 qwen3.8-27b>
```

三项缺一不可，`app/config.py` 在启动时会直接抛 `RuntimeError`。

---

## 3. 启动

**必须在 `01-llm-chat/` 目录下启动**，因为代码使用 `from app.llm import chat` 这类绝对导入。

```bash
cd /opt/ai-agent-course/01-llm-chat
source ../.venv/bin/activate

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

不激活虚拟环境也可以直接用绝对路径：

```bash
cd /opt/ai-agent-course/01-llm-chat
../.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### ⚠️ 系统代理没开时，启动要清掉代理变量

shell 里设了 `HTTPS_PROXY=http://127.0.0.1:7891`，uvicorn 会把它继承给 openai SDK。
代理客户端一旦没运行，调用大模型就会报 `openai.APIConnectionError: Connection error`
（大模型端点本身直连是通的）。启动时清掉即可：

```bash
cd /opt/ai-agent-course/01-llm-chat
env -u HTTP_PROXY -u HTTPS_PROXY -u http_proxy -u https_proxy -u ALL_PROXY -u all_proxy \
  ../.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

排查命令：

```bash
# 代理是否活着
curl -sS -o /dev/null -w '[proxy %{http_code}]\n' --max-time 5 -x http://127.0.0.1:7891 https://www.baidu.com
# 端点直连是否通（401 = 通，只是没带 key）
curl -sS --noproxy '*' -o /dev/null -w '[direct %{http_code}]\n' --max-time 15 "$LLM_BASE_URL/models"
```

启动成功的日志：

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Application startup complete.
```

停止：`Ctrl + C`。

### 其他章节的运行方式

各章都在自己目录下运行，但**入口写法分两种**，用错会报 `ModuleNotFoundError: No module named 'app'`：

| 章节 | 命令 | 原因 |
|---|---|---|
| 02 / 09 等单文件脚本 | `../.venv/bin/python app/main.py` | 脚本内不 `import app.*`，直接跑文件即可 |
| 01 / 03 / 04 / 05 / 10 / 11 | `../.venv/bin/python -m app.main` | 脚本内有 `from app.xxx import ...`，必须用 `-m` 让 `app` 成为可导入的包 |

> `python app/main.py` 会把 `sys.path[0]` 设成 `app/` 而不是章节根目录，
> 于是 `app` 这个包自己就找不到了。`-m` 才会把当前目录加进 `sys.path`。

09~11 章跑之前建议加 `HF_HUB_OFFLINE=1`（模型已缓存）并清掉代理，
两个需求在同一条命令里是冲突的——HuggingFace 要走代理，大模型端点要直连：

```bash
cd /opt/ai-agent-course/11-hybrid-search
env -u HTTP_PROXY -u HTTPS_PROXY -u http_proxy -u https_proxy -u ALL_PROXY -u all_proxy \
  HF_HUB_OFFLINE=1 ../.venv/bin/python -m app.main
```

---

## 4. 接口

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/chat` | 对话接口，入参 `{"message": "...", "session_id": "..."}`，返回 `{"answer": "..."}`。`session_id` 可省略，默认 `"default"` |
| GET | `/docs` | Swagger UI |
| GET | `/openapi.json` | OpenAPI 描述 |
| GET | `/` | 307 重定向到 `/docs`，方便浏览器直接访问 |

> 根路由是后加的。FastAPI 默认不注册 `/`，所以最初直接访问 `http://127.0.0.1:8000`
> 会返回 `{"detail":"Not Found"}`（HTTP 404）——这是正常行为，不是环境问题。
> `app/main.py` 里加了这段来兜底：
>
> ```python
> from fastapi.responses import RedirectResponse
>
> @app.get("/", include_in_schema=False)
> def root():
>     return RedirectResponse(url="/docs")
> ```
>
> `include_in_schema=False` 让这个跳转不出现在 Swagger 文档的接口列表里。

---

## 5. 测试指令

### ⚠️ 本地 curl 必须加 `--noproxy '*'`

当前 shell 设置了 `HTTP_PROXY=http://127.0.0.1:7891`，而 `NO_PROXY` 里用的是 `127.*` 这种通配写法，**curl 不识别**（curl 的 no_proxy 只认域名后缀和 CIDR），导致访问本机也会走代理并返回 `HTTP 502`。
浏览器访问 `/docs` 不受影响。

### 冒烟测试：配置与路由

```bash
cd /opt/ai-agent-course/01-llm-chat
../.venv/bin/python -c "
from app.main import app
from app.config import LLM_BASE_URL, LLM_MODEL
print('import OK')
print('base_url =', LLM_BASE_URL)
print('model    =', LLM_MODEL)
print('routes   =', [r.path for r in app.routes if r.path.startswith('/api')])
"
```

预期输出：

```
import OK
base_url = https://ws-xxxxxxxx.cn-beijing.maas.aliyuncs.com/compatible-mode/v1
model    = qwen3.8-27b
routes   = ['/api/chat']
```

### 探活

```bash
curl -sS --noproxy '*' -o /dev/null -w '[HTTP %{http_code}]\n' http://127.0.0.1:8000/docs
```

预期：`[HTTP 200]`

根路由跳转：

```bash
# 不跟随跳转，看 Location 头
curl -sS --noproxy '*' -o /dev/null \
  -w '[HTTP %{http_code}] Location: %{redirect_url}\n' http://127.0.0.1:8000/

# 跟随跳转，看最终落地页
curl -sS --noproxy '*' -L -o /dev/null \
  -w '[HTTP %{http_code}] final=%{url_effective}\n' http://127.0.0.1:8000/
```

实测输出：

```
[HTTP 307] Location: http://127.0.0.1:8000/docs
[HTTP 200] final=http://127.0.0.1:8000/docs
```

### 调用对话接口

```bash
curl -sS --noproxy '*' -w '\n[HTTP %{http_code}] time=%{time_total}s\n' \
  -X POST http://127.0.0.1:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"你好，用一句话介绍你自己"}' \
  --max-time 120
```

实测输出：

```json
{"answer":"你好，我是一名资深 Java 后端工程师，擅长基于 Spring Boot、MySQL、Redis、Elasticsearch 和 Docker 构建高可用、可扩展的后端服务。"}
```

```
[HTTP 200] time=4.905712s
```

> 首次调用耗时约 5s，属于模型推理正常范围。

---

## 6. 常见问题

| 现象 | 原因 | 处理 |
|---|---|---|
| `HTTP 502`，且 uvicorn 日志里没有该请求 | curl 走了系统 HTTP 代理 | curl 加 `--noproxy '*'` |
| `ModuleNotFoundError: No module named 'app'` | 不在 `01-llm-chat/` 目录下启动 | `cd 01-llm-chat` 后再启动 |
| `RuntimeError: LLM_API_KEY is not configured` | `.env` 缺项或未被读到 | 检查 `01-llm-chat/.env` 三个变量 |
| `openai.APIConnectionError: Connection error` | uvicorn 继承了 `HTTPS_PROXY`，但代理没在跑 | 用 `env -u HTTPS_PROXY ...` 启动，见第 3 节 |
| IDE 里 `import openai` / `import fastapi` 全标红 | 编辑器没选中 `.venv` 解释器 | 已提供 `.vscode/settings.json` 和 `pyrightconfig.json`；PyCharm 需在 Settings → Python Interpreter 手动指向 `/opt/ai-agent-course/.venv/bin/python` |
| `messages` 参数标红 `list[dict[str, str]] 不可分配给 Iterable[ChatCompletionMessageParam]` | 裸 dict 不满足 openai 的 TypedDict | 标注为 `list[ChatCompletionMessageParam]`，不要用 `# type: ignore` 掩盖 |
| `No module named ensurepip` | 系统 Python 缺 venv/pip 组件 | 用 uv（方式 A），或 `sudo apt install python3-venv` |
| venv 里只有 `Scripts/`、`Lib/` | 这是 Windows 下建的 venv | 备份后按第 1 节重建 |
| Linux 里删了几十 G，Windows 可用空间却没变 | WSL2 的 `ext4.vhdx` 只会长大不会自动缩小 | `wsl --manage <发行版> --set-sparse true`，见第 1 节 |
| `ModuleNotFoundError: No module named 'app'`，但已经 `cd` 到章节目录了 | 用了 `python app/main.py`，而该脚本内部有 `from app.xxx import` | 改用 `python -m app.main`，见第 3 节 |
| uv 报找不到 `torch==2.13.0+cpu` | uv 默认「命中第一个含该包的索引就停」，在 PyPI 上没有 `+cpu` 版本 | 安装时加 `--index-strategy unsafe-best-match` |
| `` `pypdf` package not found `` | 09 章 `PyPDFLoader` 依赖 pypdf，早期各章 requirements.txt 全部漏了它 | 已加入根 `requirements.txt`；重装即可 |
| `[Errno 101] Network is unreachable ... huggingface.co` | 清掉代理后 HF 连不上（HF 需要代理，大模型端点需要直连） | 模型已缓存时加 `HF_HUB_OFFLINE=1` 强制走本地缓存 |
| `batch size is invalid, it should not be larger than 20` | 阿里云 embedding 接口单批上限 20，而 `OpenAIEmbeddings` 默认 `chunk_size=1000` | 构造时传 `chunk_size=16` 一类的小值（09 章目前仍有此问题） |
| 访问 `http://127.0.0.1:8000` 返回 `{"detail":"Not Found"}` | 根路径 `/` 没有注册路由 | 见第 4 节，已加 `/` → `/docs` 重定向；或直接访问 `/docs` |
| `sed -i 's/xxx$/yyy/'` 改不动 `app/` 下的 py 文件 | 文件是 CRLF 行尾，`$` 锚点被 `\r` 挡住 | 用 `sed -i 's/xxx\r$/yyy\r/'`，或改用 Python 脚本改写 |
