# tmux 使用手册（WSL 后台跑服务 + 看日志）

> tmux 是终端复用器：**关掉窗口、切走标签页，会话里的进程照样跑**。
> 本仓库最典型的用法：`uvicorn` 在 tmux 里跑着，人随时切回来看日志、重启服务，
> 不用每次都用 `nohup` + `tail -f`，也不用担心 SSH/终端一关服务就断。

---

## 0. 先搞清三个层级（这是所有困惑的根源）

```
tmux server（后台服务，开机后一直驻留）
 └─ session  会话  （esapi）……你可以开好几个，互相独立
     └─ window 窗口（0:zsh 1:zsh）……一个会话里多个窗口，像浏览器标签页
         └─ pane 窗格（左右/上下分屏）……一个窗口里多块屏幕
```

- 你跑 `tmux new -s esapi`，就是「建一个叫 esapi 的会话」并钻进去。
- 底部那条绿条就是 **tmux 状态栏**，`[esapi] 0:zsh` = 当前在 esapi 会话、第 0 个窗口。
- **一切快捷键都以 `Ctrl + b` 开头**（前缀键），按完松手再按功能键。

---

## 1. 安装（Debian / Ubuntu WSL）

```bash
sudo apt update
sudo apt install -y tmux
tmux -V     # 确认装好了，会打印 tmux 3.x
```

---

## 2. 最常用的完整流程（启动服务 → 干别的 → 回来看日志）

```bash
# ① 开一个会话，跑你的服务（本仓库示例：uvicorn）
tmux new -s esapi
uvicorn app.main:app --reload          # 在里面正常前台跑，日志哗哗滚

# ② 想切走干别的？服务不能停！
#    按  Ctrl + b  然后按  d   （detach：把会话挂到后台）
#    屏幕会显示 [detached (from session esapi)]，回到普通 shell

# ③ 在任意普通终端（新标签页 / 别的机器 SSH 进来都行）：
tmux attach -t esapi                    # 重新钻回会话，日志还在、服务还活着
```

> ⚠️ **最容易踩的坑**：`tmux attach` 必须在**非 tmux 环境**里跑。
> 在 tmux 里面再 attach，会报 `sessions should be nested with care, unset $TMUX to force`。
> 这不是错误，是 tmux 的嵌套保护，无视即可；你其实已经在会话里了。

就上面这三步，能覆盖 90% 的需求。下面是速查。

---

## 3. 速查表

### 3.1 会话（session）级

| 操作 | 命令 / 按键 |
|---|---|
| 新建并进入会话 | `tmux new -s esapi` |
| 挂起当前会话（进程继续跑） | `Ctrl + b` → `d` |
| 回到已有会话 | `tmux attach -t esapi` |
| 列出所有会话 | `tmux ls`（会话死了列表里就没有） |
| 在会话里再开新会话（不推荐，容易乱） | `tmux new -s other` |
| 彻底删除会话（里面的进程会挂） | `tmux kill-session -t esapi` |
| 干掉 tmux 全部会话 | `tmux kill-server` |
| 给会话改名 | `Ctrl + b` → `$`（原会话名出现在底部，改完回车） |

### 3.2 窗口（window）级——像浏览器标签页

| 操作 | 按键 |
|---|---|
| 新建窗口 | `Ctrl + b` → `c` |
| 切下一个 / 上一个窗口 | `Ctrl + b` → `n` / `p` |
| 按编号跳窗口 | `Ctrl + b` → `0` / `1` / `2` |
| 列出并选择窗口 | `Ctrl + b` → `w` |
| 关闭当前窗口 | `Ctrl + b` → `&`（确认后关） |

> 进阶玩法：esapi 会话里开两个窗口——窗口 0 跑 `uvicorn`，窗口 1 留空跑 `curl` 测接口。
> 想看日志切回窗口 0，想敲命令切到窗口 1，互不干扰。

### 3.3 窗格（pane）级——一个窗口里分屏

| 操作 | 按键 |
|---|---|
| 左右分屏 | `Ctrl + b` → `%` |
| 上下分屏 | `Ctrl + b` → `"` |
| 光标在窗格间跳 | `Ctrl + b` → `方向键` |
| 关闭当前窗格 | `Ctrl + b` → `x` |

分屏场景：左边跑 uvicorn 日志、右边跑 curl / python，一眼看完。

### 3.4 看历史输出（日志滚太快看不到开头）

| 操作 | 按键 |
|---|---|
| 进入滚动模式（翻历史） | `Ctrl + b` → `[` |
| 翻页 | 上/下方向键、`PgUp`/`PgDn`、空格翻屏 |
| 退出滚动模式 | `q` |
| 回到底部最新输出 | 进滚动模式后按 `g` 到顶、`G` 到底 |

### 3.5 复制粘贴

1. `Ctrl + b` → `[` 进入滚动模式；
2. 移到起点按 `空格` 开始选择，方向键选中；
3. 按 `回车` 复制；
4. `Ctrl + b` → `]` 粘贴。

> 想复制到 Windows 剪贴板（粘贴到别处）：
> `Ctrl + b` → `[` 选中后按 `y`（需要装了 wl-clipboard 之类的剪贴板工具，
> WSL 下一般配 `set -g set-clipboard on` + 剪贴板工具，否则先按 `]` 粘回 tmux 再用 Ctrl+Shift+C）。

---

## 4. 停服务 / 清理现场

```bash
# 服务进程：在 tmux 里 Ctrl + C 停 uvicorn（tmux 会话本身还在，可以再起）
# 或者不进去，直接：
pkill -f "uvicorn app.main:app"

# 会话不再要了（服务已停后）：
tmux kill-session -t esapi
tmux kill-server          # 一次全清，最干净
```

> ⚠️ `--reload` 的坑：`uvicorn app.main:app --reload` 会派生子进程，
> 前台跑时在 tmux 里 `Ctrl + C` 能一次全杀；但如果用 nohup 后台跑 + reload，
> 杀主进程后子进程可能残留占用 8000 端口，用 `pkill -f "uvicorn"` 兜底清。

---

## 5. 常见问题（FAQ）

**Q1：报 `sessions should be nested with care` 是什么意思？**
你在 tmux 里又 attach 了一次 tmux。无视即可，你已经在这个会话里了。
以后 attach 命令一律从**普通终端标签页**敲。

**Q2：`tmux ls` 看不到我的 esapi 了，但 uvicorn 好像还在？**
`tmux ls` 列的是**还活着的会话**。会话被 kill / 机器重启后就没了，
但里面用 nohup / 被 kill-server 漏掉的孤儿进程可能还在。
先 `pkill -f "uvicorn"` 再重新 `tmux new -s esapi` 起服务即可。

**Q3：SSH 断了 / 关终端了，服务会不会停？**
只要 tmux 的 server 还活着就不会。这也是 tmux 相比「前台跑 uvicorn」最大的优势：
哪怕你**关掉整个终端窗口**，tmux server 继续在后台驻留，重开终端 `tmux attach` 就回来了。

**Q4：启动后想用默认的 0:zsh 窗口名，怎么改？**
`Ctrl + b` → `,` 给当前窗口改名（比如改成 `api`、`es`），好认。

**Q5：和 nohup 方案怎么选？**

| 场景 | 方案 |
|---|---|
| 临时跑一下，日志无所谓 | 直接前台跑 |
| 想服务不占终端、日志落文件、随时 tail | `nohup uvicorn ... > uvicorn.log 2>&1 &` + `tail -f uvicorn.log` |
| 要长期开发：频繁重启、看历史输出、多窗口/分屏、SSH 断线不慌 | **tmux** |

**Q6：怎么开机自启服务（让 tmux 里的 uvicorn 每次都自动起来）？**
tmux 有 `tmux new-session -d -s esapi 'uvicorn app.main:app --reload'`（-d 直接后台建会话），
配合 systemd 用户服务或 shell rc 就能实现，需要再说。

---

## 6. 一段话总结

1. 建会话：`tmux new -s esapi`，在里面跑 `uvicorn`；
2. 切走：`Ctrl + b` → `d`（服务照跑）；
3. 回来：普通终端 `tmux attach -t esapi`；
4. 清场：`pkill -f "uvicorn"` → `tmux kill-server`。
