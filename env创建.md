# 新增一章的步骤

全部章节共用仓库根目录的一个 `.venv`，**不要再给单章新建虚拟环境**。
依赖由 uv 管理，唯一事实来源是 `pyproject.toml` + `uv.lock`。

```bash
cd /opt/ai-agent-course

# 1. 建目录
mkdir -p 12-evaluation/app
touch 12-evaluation/app/__init__.py

# 2. 装新依赖
#    uv add = 装进根 .venv + 写进 pyproject.toml + 更新 uv.lock，一步到位
uv add <新包名>

# 3. 复制一份章节 pyrightconfig.json（内容各章完全一致）
cp 11-hybrid-search/pyrightconfig.json 12-evaluation/

# 4. 把新章加进根 pyrightconfig.json 的 include 和 executionEnvironments
```

提交时记得把 `pyproject.toml` 和 `uv.lock` 一起带上——少了 lock，别人 `uv sync` 出来的
就不是同一个环境了。

## ⚠️ 两个容易踩的坑

### 1. 不要用 `uv pip install` 加依赖

`uv pip install` 是 pip 的等价替代品，**不会**写进 `pyproject.toml`。
装完看着能跑，下次谁执行 `uv sync`，环境被对齐到 `uv.lock`，这个包就没了。
加依赖一律用 `uv add`。

### 2. 不要用 `pip freeze` 生成依赖清单

本仓库已经不用 `requirements.txt` 了，但这个坑值得记下来——早期每章都执行过
`pip freeze > requirements.txt`，后果是：

1. **11 份几乎一样的全量快照**，各章之间无法看出真正的差异；
2. **丢包**——某次在没装 fastapi/uvicorn 的环境里 freeze，
   把 01 章的清单覆盖掉了，导致它再也装不出一个能跑的 01 章；
   （这个坑比想象的深：那份快照连 `starlette` 都没有，而它是 FastAPI 的核心依赖。）
3. **漏包**——`pypdf` 从来没进过任何一份清单，09 章直接 `ImportError`；
4. **体积爆炸**——freeze 把 GPU 版 torch 的整套 `nvidia-*` CUDA 轮子全写了进去，
   09/10/11 三章各占 5.3GB。

根因是 `pip freeze` 记录的是「当前环境里恰好装了什么」，而依赖清单应该记录
「这个项目需要什么」。这正是现在拆成两个文件的原因：

| 文件 | 记录什么 | 谁维护 |
|---|---|---|
| `pyproject.toml` | 项目**需要**什么（19 个直接依赖） | 人（通过 `uv add`） |
| `uv.lock` | 实际**装出来**是什么（111 条，含平台条件分支） | uv 自动生成，别手改 |

`pip freeze` 把这两件事混成了一件，所以怎么用都别扭。

## 运行

见 [README.md](README.md) 第 3 节。注意有 `from app.xxx import` 的章节
必须用 `python -m app.main`，不能用 `python app/main.py`。
