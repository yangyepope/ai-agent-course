# ai-agent-course

AI Agent 课程练习项目。

| 目录 | 说明 |
|---|---|
| `01-llm-chat` | FastAPI + OpenAI 兼容接口的最小对话服务 |
| `main.py` | PyCharm 生成的模板文件，与课程无关 |

---

## 1. 环境搭建

Python 版本：**3.13**。虚拟环境统一放在仓库根目录的 `.venv`，各章节共用。

> 注意：仓库里可能残留 Windows 下创建的 `.venv`（内含 `Scripts/`、`Lib/`，`pyvenv.cfg` 指向 `D:\...`）。
> 这种 venv 在 Linux / WSL 下**不可用**，先备份再重建：
>
> ```bash
> mv .venv .venv-windows-backup
> ```

### 方式 A：uv（推荐）

系统自带的 `python3` 若没有 `pip` / `ensurepip`，用 [uv](https://github.com/astral-sh/uv) 最省事：

```bash
cd /opt/ai-agent-course

uv venv --python 3.13 .venv
VIRTUAL_ENV=.venv uv pip install -r 01-llm-chat/requirements.txt
```

### 方式 B：标准 venv + pip

```bash
cd /opt/ai-agent-course

python3 -m venv .venv
source .venv/bin/activate
pip install -r 01-llm-chat/requirements.txt
```

> 若报 `No module named ensurepip`，需先装系统包：`sudo apt install python3-venv python3-pip`，或改用方式 A。

### 依赖清单

`01-llm-chat/requirements.txt`：

```
fastapi
uvicorn[standard]
pydantic
python-dotenv
openai
```

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
| 访问 `http://127.0.0.1:8000` 返回 `{"detail":"Not Found"}` | 根路径 `/` 没有注册路由 | 见第 4 节，已加 `/` → `/docs` 重定向；或直接访问 `/docs` |
| `sed -i 's/xxx$/yyy/'` 改不动 `app/` 下的 py 文件 | 文件是 CRLF 行尾，`$` 锚点被 `\r` 挡住 | 用 `sed -i 's/xxx\r$/yyy\r/'`，或改用 Python 脚本改写 |
