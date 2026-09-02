# 新增一章的步骤

全部章节共用仓库根目录的一个 `.venv`，**不要再给单章新建虚拟环境**。

```bash
cd /opt/ai-agent-course

# 1. 建目录
mkdir -p 12-evaluation/app
touch 12-evaluation/app/__init__.py

# 2. 装新依赖（装进根 .venv）
VIRTUAL_ENV=.venv uv pip install <新包名>

# 3. 把新包【手写一行】追加到根 requirements.txt
#    注意：不要用 pip freeze 覆盖它
echo '<新包名>==<版本>' >> requirements.txt

# 4. 复制一份章节 pyrightconfig.json（内容各章完全一致）
cp 11-hybrid-search/pyrightconfig.json 12-evaluation/

# 5. requirements.txt 转发到根清单
printf -- '-r ../requirements.txt\n' > 12-evaluation/requirements.txt

# 6. 把新章加进根 pyrightconfig.json 的 include 和 executionEnvironments
```

## ⚠️ 不要用 `pip freeze > requirements.txt`

早期每章都执行了这一句，后果是：

1. **11 份几乎一样的全量快照**，各章之间无法看出真正的差异；
2. **丢包**——某次在没装 fastapi/uvicorn 的环境里 freeze，
   把 01 章的 `requirements.txt` 覆盖掉了，导致该清单再也装不出一个能跑的 01 章；
3. **漏包**——`pypdf` 从来没进过任何一份清单，09 章直接 `ImportError`；
4. **体积爆炸**——freeze 把 GPU 版 torch 的整套 `nvidia-*` CUDA 轮子全写了进去，
   09/10/11 三章各占 5.3GB。

`pip freeze` 记录的是「当前环境里恰好装了什么」，而 `requirements.txt`
应该记录「这个项目需要什么」。前者包含全部传递依赖和历史残留，后者只该有直接依赖。
新增依赖时手写一行，比 freeze 一次省事得多。

## 运行

见 [README.md](README.md) 第 3 节。注意有 `from app.xxx import` 的章节
必须用 `python -m app.main`，不能用 `python app/main.py`。
