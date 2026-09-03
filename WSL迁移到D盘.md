# WSL 从 C 盘迁移到 D 盘 / 直接装在 D 盘

> 实测环境：Windows + WSL 2.7.11.0，发行版 `Debian`（内核 6.18.33.2-2），
> 普通用户 `lipengfei`（uid 1000）。
> 起因：合并本仓 11 个虚拟环境后 Linux 侧释放了 21G，但 Windows 上的
> `ext4.vhdx` 一个字节都没缩小。

---

## 一、先搞懂问题的根源

WSL2 把整个 Linux 文件系统封装在 Windows 上的**一个虚拟磁盘文件**里：

```
C:\Users\<用户名>\AppData\Local\wsl\{<GUID>}\ext4.vhdx
```

这个文件的行为是：**只会长大，不会自动缩小。**

| | 空间 |
|---|---|
| Linux 里 `df -h /` 已用 | 31G → 9.5G（删除确实生效了） |
| Windows 上 `ext4.vhdx` 体积 | 31.28G → **31.28G（一点没变）** |

删掉的 21.7G 变成了 vhdx **内部**的空闲块。Linux 以后装东西会复用它，
所以文件不会继续变大，但 Windows 资源管理器里的可用空间**永远不会涨回来**。

### 为什么原地清理行不通（两条路都实测过）

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

实测跑完 31.28G → 31.28G。
原因：`compact vdisk` 只能回收在 vhdx 层面**被标记空闲或全零**的块。
而 ext4 删文件只改 inode，**磁盘块里的旧字节还在**，diskpart 认不出那是垃圾。
`Optimize-VHD` 同理（它同样只找全零块）。

**② `--set-sparse`：当前 WSL 版本已被微软禁用。**

```powershell
wsl --manage Debian --set-sparse true
```
```
正在进行转换，这可能需要几分钟时间。
由于潜在的数据损坏，目前已禁用稀疏 VHD 支持。
要强制发行版使用稀疏 VHD，请运行:
wsl.exe --manage <DistributionName> --set-sparse true --allow-unsafe
错误代码: Wsl/Service/E_INVALIDARG  只恢复了部分空间
```

稀疏磁盘本该让空间**自动**回收（`/` 的 `discard` 挂载参数会持续发 TRIM，
但需要稀疏 vhdx 才接得住）。它被禁用，正是现在只能手动重建的根本原因。

> **不要加 `--allow-unsafe`。** 微软是因为一个真实的数据损坏 bug 才禁用它的。
> 既然任何方案都要先导出备份，那不如直接重建——效果一样，且完全不碰这个开关。
> `.wslconfig` 里写 `[experimental] sparseVhd=true` 同理不生效。

---

## 二、两种迁移方式，先选对

| | `--manage --move` | `--export` + `--import`（本文档主方案） |
|---|---|---|
| 速度 | 快（就是搬文件） | 慢（打包 + 解包，9G 约十几分钟） |
| vhdx 体积 | **不变**（31.28G 照搬到 D 盘） | **重建，缩到实际大小**（9.57G） |
| 发行版名 | 不变 | 可保留或换新名 |
| 旧盘留备份 | 不留（原地搬走） | 可留（不执行 `unregister` 即可） |
| 适用 | 只想换盘，体积正常 | 体积已膨胀，或想留后路 |

先确认你的 WSL 支持 `--move`：

```powershell
wsl --help | findstr /i move
```

**本文档用 export/import**，因为它同时解决「换盘」和「缩容」两件事，
而且全程可回滚。如果你的 vhdx 体积正常、只是想换盘，用 `--move` 更省事：

```powershell
wsl --shutdown
wsl --manage Debian --move D:\WSL\Debian
```

---

## 三、迁移已有发行版到 D 盘（保留 C 盘作为后路）

### 前置检查

```powershell
wsl -l -v                 # 确认发行版名（本例 Debian）
wsl -d Debian -e df -h /  # 记下已用量，后面验证要对比
```

```powershell
# 目标盘可用空间：需要 ≥ 数据量 × 2（tar + 新 vhdx 同时存在）
# 本例 9.5G 数据 → 至少 20G，实际 D 盘有 711G
```

> ⚠️ **只要 C 盘的旧发行版还在，那 31.28G 就还占着。**
> 空间和后路二选一——所以删除被拆成最后一个**可选**步骤（第 6 步）。

### 第 0 步：先清缓存，别把垃圾一起搬走

在 WSL 里：

```bash
rm -rf ~/.cache/pip        # pip 下载缓存（本仓省下 3.1G）
uv cache clean             # uv 缓存
rm -rf */.mypy_cache       # 类型检查缓存
```

> `~/.cache/huggingface`（约 1.2G）**不要删**——那是 embedding / rerank 模型，
> 重下很慢。
>
> `uv cache clean` 实际只释放约 150M，因为 uv 是**硬链接**安装，大部分数据被
> `.venv` 共享着。这是正常的，不是没清干净。

清完关掉 VS Code、Claude Code 和所有连着 WSL 的终端，
否则 `wsl --shutdown` 会卡住。

### 第 1 步：导出（非破坏性，可随时中止）

```powershell
wsl --shutdown
mkdir D:\wsl-backup
wsl --export Debian D:\wsl-backup\debian.tar
```

9.5G 数据约几分钟。这一步只打包，原发行版一个字节都没动。

### 第 2 步：验证 tar（**这步不能跳**）

```powershell
dir D:\wsl-backup\debian.tar
```

实测输出：

```
2026/09/03  12:59     9,660,651,520 debian.tar
```

大小应与 `df -h /` 的已用量相当（9.5G 数据 → tar 约 9.0 GiB）。
**明显偏小（几百 MB）或上一步报错，就停在这里。**

### 第 3 步：导入为新发行版（旧的完全不动）

```powershell
mkdir D:\WSL\Debian
wsl --import Debian-D D:\WSL\Debian D:\wsl-backup\debian.tar --version 2
```

> ⚠️ **`mkdir` 这行不能省。** `wsl --import` 不会自动创建多层目标目录：
>
> ```
> 系统找不到指定的路径。
> 错误代码: Wsl/ERROR_PATH_NOT_FOUND
> ```

导入 9G 要几分钟，**过程中没有任何输出**，跑完直接回到提示符即成功。

验证：

```powershell
wsl -l -v
```

应同时列出 `Debian`（C 盘）和 `Debian-D`（D 盘）。

### 第 4 步：配置新发行版

`--import` 进来的发行版**默认用户是 root**，改回普通用户：

```powershell
wsl -d Debian-D -u root -e sh -c "printf '\n[user]\ndefault=lipengfei\n' >> /etc/wsl.conf"
wsl --set-default Debian-D
wsl --shutdown
```

> 本例 `/etc/wsl.conf` 原本只有 `[boot]` 和 `[network]` 两段，没有 `[user]`，
> 所以直接追加是安全的。**如果已有 `[user]` 段，要手动编辑而不是追加**，
> 否则会出现两个同名段。

### 第 5 步：验证

```powershell
wsl -d Debian-D -e whoami                        # → lipengfei
wsl -d Debian-D -e df -h /                       # 已用应与导出前一致
wsl -d Debian-D -e ls /opt/ai-agent-course       # 项目在不在
wsl -d Debian-D -e /opt/ai-agent-course/.venv/bin/python -c "import torch,faiss;print('ok')"
```

再确认 VS Code 能连进 `Debian-D`、项目能打开、代码能跑。

**到这里可以停下来用几天。** 有完整后路，代价是 C 盘那 31.28G 还占着。

### 第 6 步（可选）：回收 C 盘空间

只有想要那 31.28G 时才做，且确认新环境已稳定运行：

```powershell
wsl --unregister Debian
```

不可逆，但 `D:\wsl-backup\debian.tar` 还在，等于仍有完整备份。
再观察一段时间，才删 tar：

```powershell
Remove-Item D:\wsl-backup\debian.tar      # cmd 里用 del
```

### 回滚

第 6 步之前，任何时候都能退回去：

```powershell
wsl --set-default Debian          # 切回 C 盘的旧发行版
wsl --unregister Debian-D         # 不要新的了，删掉（不影响旧的）
```

### 实测结果

| | 迁移前 | 第 5 步后 | 第 6 步后 |
|---|---|---|---|
| C 盘 vhdx | 31.28G | 31.28G（留着） | **0** |
| D 盘 vhdx | — | **9.57G** | 9.57G |
| D 盘 tar | — | 9.00G | 可删 |
| C 盘可用 | 48G | 48G | **79G** |

---

## 四、全新安装：直接装到 D 盘

`wsl --install` **默认**装到 `C:\Users\<用户名>\AppData\Local\wsl\`，
而且**没有全局配置项能改这个默认值**。但较新版本的 WSL 支持在安装时直接指定位置。

### 先确认你的 WSL 支持哪些参数

```powershell
wsl --version                  # 本文档实测环境：2.7.11.0
wsl --install --help           # 看有没有 --location / --name
wsl --manage --help            # 看有没有 --move
```

按 `--install --help` 的输出选下面三个方案之一——**能用方案 A 就别折腾后两个**。

### 方案 A：`wsl --install --location`（最直接，一条命令）

如果 `wsl --install --help` 里有 `--location`：

```powershell
wsl --install Debian --location D:\WSL\Debian
```

和你在 C 盘用的 `wsl --install Debian` 是同一条命令，只是多带一个位置参数，
装完直接就在 D 盘，不需要任何后续搬迁。

配套参数：

```powershell
# --name 可以自定义发行版名（同一个发行版装多份时用）
wsl --install Debian --location D:\WSL\Debian --name Debian-D

# --no-launch 装完不自动启动（想先改配置再首次启动时用）
wsl --install Debian --location D:\WSL\Debian --no-launch
```

> ⚠️ 本文档没有在实机上验证过 `--location`（写文档时会话内无法调用 `wsl.exe`）。
> `wsl --install --help` 里能看到这个参数就用，看不到就走方案 B。

### 方案 B：先装后搬（`--location` 不可用时）

```powershell
# 1. 正常安装，但不启动
#    --no-launch 是关键：刚装完 vhdx 只有几百 MB，这时候搬最快；
#    一旦启动并开始装东西，体积上去了搬起来就慢了
wsl --install --no-launch Debian

# 2. 搬到 D 盘
wsl --manage Debian --move D:\WSL\Debian

# 3. 首次启动，创建用户
wsl -d Debian
```

需要 `wsl --manage --help` 里有 `--move`（WSL 2.0 之后才有）。

### 方案 C：下载 rootfs 直接 import（兜底，任何版本都能用）

适合 `--location` 和 `--move` 都不可用、或想完全控制安装过程的场景。

```powershell
# 1. 列出可装的发行版
wsl --list --online

# 2. 下载 rootfs tar
#    官方 rootfs 地址见各发行版文档，例如：
#    Debian:  https://salsa.debian.org/debian/WSL/-/releases
#    Ubuntu:  https://cloud-images.ubuntu.com/wsl/
#    也可以从已有机器上 wsl --export 一份干净的出来

# 3. 建目录并导入
mkdir D:\WSL\Debian
wsl --import Debian D:\WSL\Debian D:\downloads\debian-rootfs.tar --version 2

# 4. 创建普通用户（import 进来默认是 root）
wsl -d Debian -u root -e sh -c "adduser lipengfei && usermod -aG sudo lipengfei"
wsl -d Debian -u root -e sh -c "printf '\n[user]\ndefault=lipengfei\n' >> /etc/wsl.conf"
wsl --shutdown
```

### 装好后建议立刻做的配置

`/etc/wsl.conf`（发行版内部，每个发行版独立）：

```ini
[boot]
systemd=true

[network]
hostname=debian-wsl

[user]
default=lipengfei
```

`C:\Users\<用户名>\.wslconfig`（全局，对所有发行版生效）：

```ini
[wsl2]
networkingMode=mirrored
dnsTunneling=true
autoProxy=true
```

### 从第一天起就避免 vhdx 膨胀

vhdx 不会自动缩小这个问题**重建后依然存在**，所以：

- **别把大缓存放进 WSL**：pip / uv / HuggingFace 缓存都可以指到 Windows 盘，
  或者定期清理（见第 0 步）
- **别装 GPU 版 torch**（除非真要用 CUDA）：整套 `nvidia-*` 轮子约 5GB，
  CPU 版只要 1.3GB。本仓 09/10/11 三章各装一份 GPU 版，一度占了 16GB
- **多项目共用一个虚拟环境**：本仓 11 章共用根目录 `.venv`，
  从 11 个 venv（合计 18G）压到 1 个（1.4G）
- **定期检查**：`du -sh ~/.cache/*` 和 `df -h /`
- 真涨上去了，重跑本文档第三节即可

---

## 五、踩过的坑汇总

| 现象 | 原因 | 处理 |
|---|---|---|
| Linux 删了几十 G，Windows 可用空间没变 | vhdx 只会长大不会缩小 | 本文档第三节，重建 vhdx |
| `compact vdisk` 跑完体积一点没变 | ext4 空闲块非全零，diskpart 认不出 | 别用，无解 |
| `--set-sparse` 报 `E_INVALIDARG` | 微软因数据损坏 bug 已禁用 | 别用 `--allow-unsafe` |
| `wsl --import` 报 `Wsl/ERROR_PATH_NOT_FOUND` | 目标目录不存在，import 不会自动创建 | 先 `mkdir D:\WSL\Debian` |
| 导入后进去发现自己是 root | `--import` 不带用户配置 | 第 4 步写 `/etc/wsl.conf` 的 `[user]` 段 |
| Tabby / 终端里配置路径显示 `C:\Windows\system32\wsl.exe` | 那是**启动器程序**路径，所有发行版都一样 | 与数据在哪个盘无关，正常 |
| Tabby 里找不到新发行版 | 「内置」配置不出现在新建标签页菜单 | 点 `+` 右边 ▾ 选，或改自建配置的参数为 `-d Debian-D` |
| WSL 里跑 `.exe` 报 `exec format error` | 迁移后 Windows 互操作（binfmt）失效 | `wsl --shutdown` 重启即恢复 |
| `wsl --shutdown` 卡住 | VS Code / 终端还连着 | 全部关掉再试 |
| Temp 里堆着多个 `swap.vhdx` | WSL 异常退出的残留，每个 1~2G | `wsl --shutdown` 后删掉非当前会话的 |

---

## 六、排查命令

```bash
# Linux 侧实际占用
df -h /
du -sh ~/.cache/* | sort -rh | head

# 从 WSL 里查看 Windows 上 vhdx 的真实体积（路径换成自己的）
V="/mnt/d/WSL/Debian/ext4.vhdx"
awk -v b="$(stat -c %s "$V")" 'BEGIN{printf "%.2f GB\n", b/1073741824}'

# 不知道旧 vhdx 的 GUID 时才用 find 去搜（扫 C 盘很慢，加 timeout 兜底）
timeout 60 find /mnt/c/Users -maxdepth 6 -iname 'ext4.vhdx' 2>/dev/null
```

```powershell
wsl -l -v                          # 发行版列表、状态、版本
wsl --version                      # WSL 自身版本
wsl --manage Debian --help         # 看当前版本支持哪些管理操作
```

> 两个 `df` 数字对不上时，**先看 vhdx 体积**——它才是 Windows 真正在意的那个数。
