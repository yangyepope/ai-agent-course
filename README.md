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
| Linux 里 `df -h /` 的已用 | 31G → 9.5G（确实释放了） |
| Windows 上 `ext4.vhdx` 的体积 | 31.3G → 31.3G（**一点没变**） |

那 17G 只是变成了 vhdx **内部**的空闲块，Linux 写新文件会复用，
但 Windows 资源管理器里的可用空间不会涨。

#### 先清缓存，再谈磁盘

重建磁盘之前先把数据压到最小，否则等于把垃圾一起搬走：

```bash
rm -rf ~/.cache/pip                    # pip 下载缓存，可删（本仓省下 3.1G）
uv cache clean                         # uv 缓存，可删
rm -rf */.mypy_cache                   # 类型检查缓存，可删
```

> `~/.cache/huggingface`（约 1.2G）**不要删**——那是 09~11 章的 embedding /
> rerank 模型，重下很慢。
>
> `uv cache clean` 实际只释放约 150M，因为 uv 是**硬链接**安装，
> 大部分数据被 `.venv` 共享着。这是正常的，不是没清干净。

#### 方案 A：迁到 D 盘 + 重建 vhdx（旧发行版保留为后路）

思路：把数据导出成 tar，在 D 盘**导入成一个新名字的发行版**，C 盘那个
原封不动留着。全程不执行 `wsl --unregister`，任何一步出问题都能退回去。

> ⚠️ **只要 C 盘的旧发行版还在，那 31.28G 就还占着。**
> 空间和后路二选一——所以删除被拆成最后一个**可选**步骤（第 7 步），
> 等在新环境里用顺手了再决定。

| | 现在 | 第 6 步后 | 第 7 步后 |
|---|---|---|---|
| C 盘 vhdx | 31.28G | 31.28G（留着） | **0** |
| D 盘 vhdx | — | 约 10G | 约 10G |
| D 盘 tar | — | 约 9.5G | 可删 |

**第 0 步：准备**

关掉 VS Code、Claude Code 和所有连着 WSL 的终端，否则 `--shutdown` 会卡住。
先在 WSL 里清掉可删缓存（见上一节），别把垃圾一起搬走。

**第 1 步：导出**（非破坏性，可随时中止）

```powershell
wsl --shutdown
mkdir D:\wsl-backup
wsl --export Debian D:\wsl-backup\debian.tar
```

**第 2 步：验证 tar（这步不能跳）**

```powershell
dir D:\wsl-backup\debian.tar
```

大小应与 `df -h /` 的已用量相当（本仓 9.5G 数据 → tar 约 8~11G）。
明显偏小或上一步报错，就停在这里。

**第 3 步：导入为新发行版**（旧的完全不动）

```powershell
wsl --import Debian-D D:\WSL\Debian D:\wsl-backup\debian.tar --version 2
```

此时 `wsl -l -v` 会同时列出 `Debian`（C 盘）和 `Debian-D`（D 盘）。

**第 4 步：配置新发行版**

`--import` 进来的发行版默认用户是 root，改回普通用户：

```powershell
wsl -d Debian-D -u root -e sh -c "printf '\n[user]\ndefault=lipengfei\n' >> /etc/wsl.conf"
wsl --set-default Debian-D
wsl --shutdown
```

> 本仓的 `/etc/wsl.conf` 只有 `[boot]` 和 `[network]` 两段，没有 `[user]`，
> 直接追加是安全的。

**第 5 步：验证**

```powershell
wsl -d Debian-D -e whoami                        # 应输出 lipengfei
wsl -d Debian-D -e df -h /                       # 已用应与导出前一致
wsl -d Debian-D -e ls /opt/ai-agent-course
wsl -d Debian-D -e /opt/ai-agent-course/.venv/bin/python -c "import torch,faiss;print('ok')"
```

再确认 VS Code 能连进 `Debian-D`、项目能打开、代码能跑。

**第 6 步：切换日常使用**

第 4 步的 `--set-default` 已经让 `wsl` 默认进 `Debian-D`。
VS Code 需要在 *WSL: Connect to WSL using Distro…* 里显式选 `Debian-D`。

> ⚠️ **两个发行版从导出那一刻起就各走各的。** 在 `Debian-D` 里改的东西
> 不会同步回 `Debian`，反之亦然。确认切换后就别再进旧的，否则改动会分叉。

**第 7 步（可选）：回收 C 盘空间**

只有想要那 31.28G 时才做。做之前确保新环境已经用了几天、没有任何问题：

```powershell
wsl --unregister Debian
```

这一步不可逆，但 `D:\wsl-backup\debian.tar` 还在，等于仍有一份完整备份。
再等一段时间确认无误，才删 tar：

```powershell
Remove-Item D:\wsl-backup\debian.tar
```

**回滚**

第 7 步之前，任何时候都能退回去：

```powershell
wsl --set-default Debian          # 切回 C 盘的旧发行版
wsl --unregister Debian-D         # 不想要新的了，删掉它（不影响旧的）
```

> 注意：重建后的新 vhdx **以后照样不会自动缩小**（稀疏磁盘被禁用这点没变），
> 所以别把大缓存（pip / uv / GPU 版 torch）堆回 WSL 里。真需要清的时候，
> 重跑一遍本流程即可。

#### 走不通的两条路（实测，别浪费时间）

**① `diskpart` → `compact vdisk`：无效。**

```powershell
wsl --shutdown
diskpart
```
```
select vdisk file="C:\Users\<用户名>\AppData\Local\wsl\{<GUID>}\ext4.vhdx"
attach vdisk readonly
compact vdisk
detach vdisk
exit
```

实测跑完 vhdx 从 31.28G → 31.28G，一个字节没回收。
原因：`compact vdisk` 只能回收在 vhdx 层面**被标记空闲或全零**的块，
而 ext4 删文件只改 inode，**磁盘块里的旧字节还在**，diskpart 不敢动。
`Optimize-VHD` 同理也没用（它同样只找全零块）。

**② `--set-sparse`：当前 WSL 版本已被微软禁用。**

```powershell
wsl --manage Debian --set-sparse true
```

WSL 2.7.11 上直接报错中止：

```
由于潜在的数据损坏，目前已禁用稀疏 VHD 支持。
要强制发行版使用稀疏 VHD，请运行:
wsl.exe --manage <DistributionName> --set-sparse true --allow-unsafe
错误代码: Wsl/Service/E_INVALIDARG  只恢复了部分空间
```

**不要加 `--allow-unsafe`。** 微软是因为一个真实的数据损坏 bug 才禁用它的，
为了几十 G 去冒丢整个 WSL 磁盘的风险不值得。`.wslconfig` 里写
`[experimental] sparseVhd=true` 同理不生效。

> 稀疏磁盘本该让空间**自动**回收（`discard` 挂载参数发出的 TRIM 需要稀疏
> vhdx 才接得住）。它被禁用，正是现在只能靠方案 A 手动重建的根本原因。

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

# 从 WSL 里查看 Windows 上 vhdx 的真实体积（路径换成自己的）
V="/mnt/c/Users/<用户名>/AppData/Local/wsl/{<GUID>}/ext4.vhdx"
awk -v b="$(stat -c %s "$V")" 'BEGIN{printf "%.1f GB\n", b/1073741824}'

# 不知道 GUID 时才用 find 去搜（要扫整个 C 盘，很慢，加 timeout 兜底）
timeout 60 find /mnt/c/Users -maxdepth 6 -iname 'ext4.vhdx' 2>/dev/null

# 发行版名
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
| Linux 里删了几十 G，Windows 可用空间却没变 | WSL2 的 `ext4.vhdx` 只会长大不会自动缩小，且 `compact vdisk` / `--set-sparse` 均无效 | 导出后重建 vhdx，见第 1 节 |
| `ModuleNotFoundError: No module named 'app'`，但已经 `cd` 到章节目录了 | 用了 `python app/main.py`，而该脚本内部有 `from app.xxx import` | 改用 `python -m app.main`，见第 3 节 |
| uv 报找不到 `torch==2.13.0+cpu` | uv 默认「命中第一个含该包的索引就停」，在 PyPI 上没有 `+cpu` 版本 | 安装时加 `--index-strategy unsafe-best-match` |
| `` `pypdf` package not found `` | 09 章 `PyPDFLoader` 依赖 pypdf，早期各章 requirements.txt 全部漏了它 | 已加入根 `requirements.txt`；重装即可 |
| `[Errno 101] Network is unreachable ... huggingface.co` | 清掉代理后 HF 连不上（HF 需要代理，大模型端点需要直连） | 模型已缓存时加 `HF_HUB_OFFLINE=1` 强制走本地缓存 |
| `batch size is invalid, it should not be larger than 20` | 阿里云 embedding 接口单批上限 20，而 `OpenAIEmbeddings` 默认 `chunk_size=1000` | 构造时传 `chunk_size=16` 一类的小值（09 章目前仍有此问题） |
| 访问 `http://127.0.0.1:8000` 返回 `{"detail":"Not Found"}` | 根路径 `/` 没有注册路由 | 见第 4 节，已加 `/` → `/docs` 重定向；或直接访问 `/docs` |
| `sed -i 's/xxx$/yyy/'` 改不动 `app/` 下的 py 文件 | 文件是 CRLF 行尾，`$` 锚点被 `\r` 挡住 | 用 `sed -i 's/xxx\r$/yyy\r/'`，或改用 Python 脚本改写 |
