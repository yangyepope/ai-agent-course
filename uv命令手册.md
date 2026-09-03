# uv 命令手册

本仓库的依赖由 [uv](https://docs.astral.sh/uv/) 管理，事实来源是
[pyproject.toml](pyproject.toml) + `uv.lock`，**没有 `requirements.txt`**。
本文按「日常用什么」到「偶尔要查什么」排列。当前版本 uv 0.12.7。

---

## 0. 先搞清一件事：uv 有两套接口

这是所有困惑的根源。uv 同时提供两套互不相干的命令：

| | 命令 | 依赖记在哪 | 什么时候用 |
|---|---|---|---|
| **项目接口** | `uv add` / `uv sync` / `uv lock` / `uv run` | `pyproject.toml` + `uv.lock` | **本仓库一律用这套** |
| **pip 兼容层** | `uv pip install` / `uv pip list` / `uv pip freeze` | 哪也不记，装完就完 | 只在临时试包、或迁移老项目时用 |

> ⚠️ **最容易踩的坑**：`uv pip install elasticsearch` 能装上、能 import、能跑，
> 但它**不会写进 `pyproject.toml`**。下次任何人执行 `uv sync`，环境被对齐到 `uv.lock`，
> 这个包就被删掉了，而且报错发生在几天后、在别人机器上。
>
> **加依赖一律用 `uv add`。**

---

## 1. 最常用的五条

```bash
uv sync                        # 建/对齐环境到 uv.lock（clone 完第一件事）
uv add <包名>                  # 加依赖
uv remove <包名>               # 删依赖
uv run python -m app.main      # 跑脚本，不用 activate
uv tree                        # 看依赖树，查「这个包是谁拖进来的」
```

九成的日常操作就这五条。

---

## 2. 环境

### `uv sync` —— 把环境对齐到 lock

```bash
uv sync                  # 标准用法：装 dependencies + dev 组
uv sync --no-dev         # 只装运行时依赖，不装 pyright（部署时用）
uv sync --frozen         # 严禁改动 uv.lock，lock 过期就直接报错（CI 用这个）
uv sync --locked         # 类似 --frozen，但会先校验 lock 与 pyproject 是否一致
uv sync --reinstall      # 全部重装一遍，怀疑环境被手工污染时用
uv sync --dry-run        # 只打印会做什么，不真的动手 ← 很有用
```

它是**幂等**的，也是**双向**的：多的包会被删掉、少的装上、版本不对的换掉。
所以「装完东西发现不见了」多半是因为那个包不在 `pyproject.toml` 里。

`.venv` 不存在时它会自动创建，`requires-python` 指定的 Python 版本不在机器上时会自动下载。
**不需要手工 `uv venv`，也不需要 `activate`。**

### 手工建 venv（一般用不到）

```bash
uv venv                        # 按 pyproject 的 requires-python 建 .venv
uv venv --python 3.13 .venv    # 指定版本和路径
```

> uv 建的 venv 里**没有 pip**。所以在激活状态下敲裸 `pip`，命令会落到系统 Python 上，
> 在 Debian / Ubuntu 上直接报 `error: externally-managed-environment`。
> 这不是环境坏了，是你不该用 pip。

### Python 版本

```bash
uv python list                 # 看机器上有哪些 Python（含 uv 自己管的）
uv python install 3.13         # 装一个，不碰系统 Python
uv python find                 # 当前项目会用哪个
uv python pin 3.13             # 写一个 .python-version 文件钉住版本
```

---

## 3. 依赖

### 加

```bash
uv add elasticsearch                   # 最常见
uv add 'elasticsearch>=9,<10'          # 带版本约束（引号别漏，shell 会吃掉 > <）
uv add --dev pyright                   # 开发期工具，进 [dependency-groups] 的 dev 组
uv add --group docs mkdocs             # 自定义分组
uv add 'uvicorn[standard]'             # 带 extra
uv add --upgrade-package langchain     # 顺便把某个包升到最新
```

`uv add` 一条命令做三件事：写 `pyproject.toml` → 更新 `uv.lock` → 装进 `.venv`。

**改完把 `pyproject.toml` 和 `uv.lock` 一起提交**，少了 lock，别人 `uv sync` 出来的就不是同一个环境。

### 删

```bash
uv remove jieba
uv remove --dev pyright
```

会连带把不再需要的传递依赖一起清掉。

### 升级

```bash
uv lock --upgrade                      # 全部升到约束允许的最新，只改 lock 不装
uv lock --upgrade-package langchain    # 只升一个 ← 推荐，可控
uv sync                                # 然后同步到环境
```

> `uv lock --upgrade` 一次动几十个包，出问题很难定位。日常用 `--upgrade-package` 逐个来。

### 看

```bash
uv tree                        # 依赖树
uv tree --depth 1              # 只看直接依赖
uv tree --package torch        # torch 的依赖
uv tree --invert --package numpy   # 反向：谁依赖了 numpy ← 排查冲突神器
uv pip list                    # 当前环境装了什么（扁平列表）
uv pip show fastapi            # 单个包的详情
```

### 审计

```bash
uv audit                       # 查已知漏洞（0.12 起内置，不用装 pip-audit）
```

---

## 4. 运行

```bash
uv run python -m app.main              # 推荐：自动确保环境是最新的
uv run uvicorn app.main:app --reload
uv run pyright                         # 跑 dev 组里的工具
uv run --no-sync python -m app.main    # 跳过同步检查，快一点
```

`uv run` 会先隐式做一次 `uv sync`，所以你永远不会在过期环境上跑代码。

老办法也一样能用：

```bash
source .venv/bin/activate
python -m app.main
```

> 本仓库有 `from app.xxx import` 的章节**必须**用 `python -m app.main`，
> 不能用 `python app/main.py`，否则 `ModuleNotFoundError: No module named 'app'`。

---

## 5. 一次性工具（不进项目依赖）

```bash
uvx ruff check .               # 临时跑一次，跑完不留痕迹（uvx = uv tool run）
uv tool install ruff           # 全局装一个命令行工具
uv tool list                   # 看装了哪些
uv tool upgrade --all
uv tool uninstall ruff
```

用它装 `ruff`、`httpie`、`pre-commit` 这类**跟项目无关的命令行工具**，
它们各自跑在独立环境里，不会污染 `.venv`，也不会进 `pyproject.toml`。

---

## 6. 本项目特有的：CPU 版 torch

`torch==2.13.0+cpu` 只存在于 PyTorch 官方索引，PyPI 上没有。[pyproject.toml](pyproject.toml) 里是这么配的：

```toml
[[tool.uv.index]]
name = "pytorch-cpu"
url = "https://download.pytorch.org/whl/cpu"
explicit = true          # 只有下面显式指过来的包走这个索引，其余一律走 PyPI

[tool.uv.sources]
torch = { index = "pytorch-cpu" }
```

`explicit = true` 是关键。没有它就得给整个解析过程开 `--index-strategy unsafe-best-match`，
那会让**每个**包都去 PyTorch 索引碰一次运气（慢，且有装错包的风险）。现在只有 torch 走那条路。

**别手工改 torch 版本**，改完 `uv lock` 可能把 GPU 版拉进来，多带约 5GB 的 `nvidia-*` 依赖。

---

## 7. 缓存 / 网络

```bash
uv cache dir                   # 缓存在哪（默认 ~/.cache/uv）
uv cache size                  # 多大
uv cache prune                 # 清理失效条目 ← 安全，日常用这个
uv cache clean                 # 全清，下次要重新下载全部
uv cache clean torch           # 只清一个包
```

网络相关的环境变量：

```bash
UV_HTTP_TIMEOUT=600 uv sync    # torch 的 wheel 约 200MB，默认 30s 超时不够
UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple uv sync   # 换国内镜像
```

> ⚠️ 换镜像时注意：清华源没有 `+cpu` 版的 torch。它由 `[tool.uv.sources]` 单独指到
> PyTorch 官方索引，不受 `UV_INDEX_URL` 影响，所以这条能正常工作——但那 200MB 走的是境外线路。

---

## 8. 导出（本仓库不用，但要知道有）

```bash
uv export --format requirements-txt --no-hashes -o requirements.txt
```

给没有 uv 的人用。本仓库**已刻意删掉** `requirements.txt`，原因见 [env创建.md](env创建.md)。

> 如果哪天要恢复：`uv export` **不会**输出 `--extra-index-url`，
> 导出的清单里 `torch==2.13.0+cpu` 在 PyPI 上不存在，pip 会直接失败，需要手工把那行补进文件头部。

---

## 9. 维护 uv 自己

```bash
uv self update                 # 升级 uv
uv self version                # 看版本
```

---

## 10. 排错速查

| 现象 | 原因 | 怎么办 |
|---|---|---|
| `error: externally-managed-environment` | 用了裸 `pip`。uv 建的 venv 里没有 pip，命令落到系统 Python 上，Debian 按 PEP 668 禁止往系统目录装包 | 改用 `uv add` / `uv sync`。**别加 `--break-system-packages`** |
| 装好的包 `uv sync` 之后不见了 | 用了 `uv pip install`，没写进 `pyproject.toml` | 用 `uv add` 重装一次 |
| `Failed to download torch ... network timeout (30s)` | wheel 约 200MB，默认超时不够 | `UV_HTTP_TIMEOUT=600 uv sync`，已下的部分有缓存，重试不从头来 |
| 找不到 `torch==2.13.0+cpu` | PyPI 上没有 `+cpu` 版本 | 确认 `pyproject.toml` 里 `[[tool.uv.index]]` + `[tool.uv.sources]` 两段都在 |
| `uv sync` 报 lock 过期 | 有人改了 `pyproject.toml` 却没提交 `uv.lock` | `uv lock` 重新生成并提交 |
| 想知道某个包是谁拖进来的 | | `uv tree --invert --package <包名>` |
| 环境被手工搞乱了 | | `uv sync --reinstall`，或 `rm -rf .venv && uv sync` |

---

## 11. pip → uv 对照表

| pip / venv | uv |
|---|---|
| `python -m venv .venv` | `uv venv`（或直接 `uv sync`，会自动建） |
| `source .venv/bin/activate` | 不需要，用 `uv run` |
| `pip install X` | `uv add X` |
| `pip install -r requirements.txt` | `uv sync` |
| `pip uninstall X` | `uv remove X` |
| `pip list` | `uv pip list` |
| `pip freeze > requirements.txt` | `uv lock`（然后提交 `uv.lock`） |
| `pip install --upgrade X` | `uv lock --upgrade-package X && uv sync` |
| `pipx install X` | `uv tool install X` |
| `pipx run X` | `uvx X` |
| `pip-audit` | `uv audit` |
