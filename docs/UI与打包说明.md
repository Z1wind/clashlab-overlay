# ClashLab UI 与打包说明

> 本文只描述代码可证实或已实测的内容；仍未验证的项（如杀软是否误报、hex 色值、quad 落点像素）标注「待实测确认」。
> 工程根目录：`C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat`，下文路径除特别说明外均相对该根目录。

## 1. 如何 Build

### 前置环境

- Python 3.13.5 安装在 `D:\Python313`（解释器 `D:\Python313\python.exe`）；
- PyInstaller 6.22.3（`python -m PyInstaller --version` 已核实）；
- `tkinter`、`Pillow`（13.0.0）在该解释器下可正常导入。

### 执行打包

方式一：直接跑脚本（脚本内部先清理 `build\`、`dist\ClashLab\`，再调用 PyInstaller，最后校验 exe 存在）：

```powershell
cd "C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
.\build_exe.ps1
```

方式二：手动执行同一命令：

```powershell
cd "C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
& "D:\Python313\python.exe" -m PyInstaller --noconfirm clashlab.spec
```

打包模式为 onedir（`clashlab.spec` 中 `exclude_binaries=True` + `COLLECT`），产物为：

- `dist\ClashLab\ClashLab.exe`（主程序，窗口模式 `console=False`、`debug=False`、`upx=False`）；
- 依赖与数据落在 `dist\ClashLab\_internal\` 下。

实测产物（已打包核验）：

- `ClashLab.exe` 5,533,341 字节（约 5.3 MB）；整个 `dist\ClashLab\` 约 200.5 MB；
- build 日志结论 `Build complete!`；warn 文件中的 missing module 均为 numpy/PIL 的可选条件导入（可选模块），无致命项；
- `assets\coc`、`layouts`、`config` 已核验进入包内（`_internal\` 下可见 `th13_sample.json`、`config\ui.json`、`assets\coc\manifest.json`）；
- 首次启动实测在 8~15s 内出窗存活。

**`build_exe.ps1` 编码坑（改脚本时必读）**：旧版脚本为 UTF-8 无 BOM 且含中文，本机 PowerShell 按 GBK 解析会报 `ParserError: Unexpected token`，PyInstaller 根本没被执行；现版已改为纯 ASCII 输出 + `$PSScriptRoot` 推导工程根（不再硬编码中文路径字面量）。**修改该脚本时不要重新引入中文或任何非 ASCII 字符**，否则会再次解析失败。

### 源码运行

无命令行参数时进入 GUI；带参数时转给 CLI（`launch.py` / `clashlab\__main__.py` 两条入口等价）：

```powershell
cd "C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
& "D:\Python313\python.exe" -m clashlab
```

## 2. 资源如何解析

`clashlab.spec` 的 `datas` 把工程下的 `assets\`、`layouts\`、`config\` 三个目录整体打进包（存在才收）。运行时：

- 冻结态（exe）：`app.py` 的 `res_path()` 取 `sys._MEIPASS` 为基准拼资源路径；`launch.py` 在 `sys.frozen` 时把 `_MEIPASS` 插入 `sys.path`。PyInstaller 6.x onedir 下 `sys._MEIPASS` 指向 `dist\ClashLab\_internal\`（不是 exe 同级目录），资源在 `_internal\` 内按原相对目录存放；
- 源码态：基准为工程根目录（`ROOT = app.py` 中 `__file__` 上溯两级）。

输出目录另走 `out_path()`：冻结态写到 **exe 同级**的 `out\`（注意：写输出与读资源是两个基准，别混淆），源码态写到工程根的 `out\`。

两条路径的差异：

| 场景 | 资源读取基准 | `out\` 写入位置 |
| --- | --- | --- |
| 源码运行 | 工程根目录 | 工程根 `out\` |
| exe 运行 | `sys._MEIPASS`（即 `dist\ClashLab\_internal\`） | exe 同级 `out\` |

工程外启动已实测通过：从空目录 `E:\Temp\clashlab_cwd_test`（本机 TEMP 映射在 E 盘）启动 exe，进程存活 15s、资源正常，证明运行不依赖 CWD。

**不能在代码里写死相对路径**：双击或快捷方式启动时工作目录（CWD）不是工程根，`open("assets/...")` 这类相对 CWD 的写法在源码态和打包态都会漂移；必须以 `_MEIPASS` / `__file__` 上溯得到的包根为基准。

## 3. 已知限制

- **首次启动偏慢**：PyInstaller 首次解包/初始化开销所致，实测 exe 在 8~15s 内出窗存活；同进程内重复启动不受影响。
- **杀软误报**：PyInstaller 产物常见启发式误报，处理方式为加入白名单/提交厂商，不影响程序本身；本机是否触发误报**待实测确认**。
- **缺 assets**：`assets\coc\` 缺失时，模板匹配（`assets.match_buildings`）取不到模板即跳过、不抛异常；`STATS` 数值表是代码内联的，离线研究计算不受影响。
- **adb 未连接时实时页降级**：「连接/体检」失败只记日志、状态灯显示「● 连接失败」；「开始监视」连接失败直接退出循环、不刷屏；画面区保持「等待画面…」占位。研究、采集、设置三页不依赖 adb 在线。
- **战术中枢窗口必须挂主窗口**：中枢小窗通过 `attach(master)` 挂到主窗口，不要自建第二个 Tk 实例；Windows 上自建第二实例会触发 Tcl apartment 错误，这与「弹出战术中枢」按钮的稳定性直接相关。

## 4. 提示词三档（研究页大模型复核）

三档定义在 `clashlab\prompts.py` 的 `STYLES` 字典（**以该字典为准**；模块顶部 docstring 旧值 320/560/720 未同步，勿用）：

| 档位 | 界面标签 | max_tokens | 适用场景与输出要求 |
| --- | --- | --- | --- |
| `terse` | 精简（快） | 340 | 只给结论、必要修正和首打顺序；不复述输入、不分点解释。快速过方案时用 |
| `coach` | 教练（讲理由） | 600 | 每条 `entry_adjust` 给一句可执行理由，`notes` 给打法节奏建议。学打法时用 |
| `audit` | 审计（挑错） | 760 | 逐条检查三个方案的逻辑错误（入点贴角、双线夹角、承伤超血量），允许 verdict 否定规则引擎，但必须给替代入点和理由。怀疑规则引擎漏检时用 |

**切换方式**：研究页工具栏的样式下拉（readonly Combobox，选项来自 `prompts.style_names()`），默认 `terse`；切换后日志打印新档位与 `max_tokens`。

**缓存行为**：缓存键 = 阵型文件名 + 方案 + 档位（+ 模型提示）的 SHA1 前 16 位，落盘 `out\llm_cache\*.json`，TTL 7200 秒（2 小时）。命中时界面显示「缓存命中 0.0s」，不重复调用模型、不重复计费；**档位不同即缓存键不同**，切档会 miss 重新调用。

实测（源码态）：terse / coach / audit 三档各复核一次，均出卡并通过校验，把握度分别为 0.78 / 0.71 / 0.68；截图与全文见 `out\ui\review_terse.png`、`review_coach.png`、`review_audit.png`（同名 `.txt` 为复核全文）。

## 5. 四页功能速览

- **实时**：输入序列号（默认 `127.0.0.1:5555`）连接/体检、开始/停止监视（ADB 只读抓帧，默认不下发任何点击），展示当前画面、状态/标定/帧耗时/置信度与日志；可弹出战术中枢小窗。
- **研究**：选阵型 JSON →「生成研究」（覆盖/弱侧/入点/首打顺序，产物 `out\study\study.png`、`study.json`）→「大模型复核」（三档可选）；可打开研究图。
- **采集**：跑一轮/连续 10 轮 sample 模式侦察截图入库，模型给阵型打标签，失败样本标待人工确认；可打开样本目录。页面有封号风险提示，真实账号自动化可能触发 Supercell 封禁。
- **设置**：改 ADB 路径、序列号、模型、输出目录并保存到 `config\ui.json`；「测试模型」走 `llm.ping()`；环境区显示 Python 版本、打包模式（EXE/源码）、资源目录。

## 6. 常见故障排查

**缺 tkinter 或 PIL 依赖**：`clashlab.spec` 的 `hiddenimports` 已含 `tkinter`、`tkinter.filedialog/messagebox/ttk`、`PIL.ImageTk`。若仍报 `ModuleNotFoundError`，把缺失模块补进 `hiddenimports` 后重跑 `.\build_exe.ps1`；源码侧确认 `pip install Pillow`，tkinter 随官方 Python 安装。

**窗口黑屏/白屏**：打包态 `console=False` 无控制台，先源码运行复现：

```powershell
cd "C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
& "D:\Python313\python.exe" -m clashlab
```

看终端报错。画面区显示「等待画面…」/「尚未生成」是未就绪占位，不是黑屏故障；字体缺失时 UI 层会回退 Arial/默认字体。

**adb 端口连不上**：手动核验（adb 实测路径 `E:\leidian\LDPlayer9\adb.exe`）：

```powershell
& "E:\leidian\LDPlayer9\adb.exe" devices
& "E:\leidian\LDPlayer9\adb.exe" connect 127.0.0.1:5555
```

`ensure_device()` 会自动尝试 `127.0.0.1:5555 / 5557 / 5559`；多开模拟器端口在雷电设置内查看。adb 路径也可用环境变量 `CLASHLAB_ADB` 覆盖。

## 7. 坐标标注（draw_calls 契约）

> 本节描述契约、语义与用法；UI 绘制实现与本文是并行流水线，具体函数内部细节可能微调。未亲眼验证的像素效果与条数均标注「待实测确认」。

UI 侧可把大模型策略以屏幕绘制方式标出坐标点：标记建筑、女王穿云箭落点/路径、英雄与部队投放点、法术圈。数据源为统一契约 `draw_calls`，JSON 落盘读取，**契约只读、字段固定**。

### 7.1 契约结构

顶层 `version: 1`，含五个数组：

| 数组 | 用途 | 字段 | 取值约束 |
| --- | --- | --- | --- |
| `marks` | 建筑标记 | `kind` / `tile` / `label` / `role` / `seq` | `role` ∈ `target` \| `snipe` \| `avoid` |
| `lines` | 穿云箭 | `kind` / `from` / `to` / `hits` / `label` | `kind` 固定 `giant_arrow`；`hits` 为被穿坐标点数组 `[[x,y],...]` |
| `pins` | 投放点 | `kind` / `role` / `tile` / `count` / `order` / `label` | `kind` ∈ `hero` \| `troop` \| `spell`；`role` ∈ `queen` \| `king` \| `warden` \| `rc` \| `edrag` \| `freeze` |
| `circles` | 法术圈 | `kind` / `tile` / `radius` | `kind` ∈ `freeze` \| `rage` \| `invis` |
| `steps` | 执行顺序 | 规则侧为字符串列表；兼容 `{order, text}` 对象 | — |

简短示例：

```json
{
  "version": 1,
  "marks": [{ "kind": "building", "tile": [32, 32], "label": "散射炮", "role": "snipe", "seq": 1 }],
  "lines": [{ "kind": "giant_arrow", "from": [1, 11], "to": [22, 32], "hits": [[12, 22], [22, 32]], "label": "穿云箭 穿过2座防空" }],
  "pins": [{ "kind": "hero", "role": "queen", "tile": [8, 16], "count": 1, "order": 1, "label": "女王" }],
  "circles": [{ "kind": "freeze", "tile": [24, 24], "radius": 3 }],
  "steps": ["女王 (1,11) 朝 (22,32) 放穿云箭，穿过 2 座防空"]
}
```

### 7.2 颜色语义

| 对象 | 角色 | 视觉 |
| --- | --- | --- |
| 建筑 `marks` | `target` | 琥珀实线框 |
| 建筑 `marks` | `snipe` | 青色虚线框 |
| 建筑 `marks` | `avoid` | 珊瑚斜线框 |
| 投放点 `pins` | `queen` | 青 |
| 投放点 `pins` | `king` | 橙 |
| 投放点 `pins` | `warden` | 紫灰 |
| 投放点 `pins` | `rc` | 珊瑚 |
| 投放点 `pins` | `troop` | 绿 |
| 法术圈 `circles` | `freeze` | 冰蓝 |
| 法术圈 `circles` | `rage` | 品红 |
| 法术圈 `circles` | `invis` | 白 |

HUD 左下角附图例说明各色含义；具体 hex 色值与线型实际效果**待实测确认**。

### 7.3 坐标换算

tile → 屏幕像素统一走 `clashlab\geo.py` 的 `Calib.tile_to_px(gx, gy)`，不要自己推像素公式。`Calib` 可由 `Calib.from_quad(quad)` 或 `Calib.from_dict(...)` 构造。实测 quad 示例 `[[697,107],[944,351],[672,585],[347,327]]`（对应底图 `out\live_00.png`）；该 quad 下的实际落点像素**待实测确认**。

### 7.4 如何换数据源

- 正式数据由算法侧 `clashlab\plan_marks.py` 的 `build_marks` 产出，落 `out\marks\marks.json`；当前 `marks.json` 已是真实规则数据（`source=rule`：6 条 marks、1 条 `giant_arrow` 穿 2 个防空、6 个 pins（queen/king/warden/rc 四个英雄 + 雷龙两批 ×3/×4）、1 个 freeze 圈、6 条 steps）；
- `out\marks\marks_demo.json` 现在仅作异常兜底，正常路径不再使用；
- 换数据源只需替换该 JSON 或把 `build_marks` 接进来，UI 侧字段不用改。

**`steps` 两种形态兼容**：规则侧产出的是字符串列表；demo/手写数据可能带 `{order, text}` 对象，UI 已做归一，两种都能被接受。

### 7.5 研究页按钮与产物

研究页三个按钮：**生成标注**、**推送到 HUD**、**导出标注图**。证据截图落在 `out\ui\`：`marks_preview.png`（底图标注）、`hud_marks.png`（HUD 叠标 + 图例）、`marks_export.png`（导出图）、`panel_marks.png`（面板执行顺序 6 条热区）。小窗面板「执行顺序」区最多显示 6 条，点击某步高亮该步 2 秒。

## 附：关键路径表

| 用途 | 路径（相对工程根目录） |
| --- | --- |
| 打包规格 | `clashlab.spec` |
| 打包脚本 | `build_exe.ps1` |
| 入口 | `launch.py`、`clashlab\__main__.py` |
| 内置资源 | `assets\coc\`、`layouts\`、`config\` |
| exe 产物 | `dist\ClashLab\ClashLab.exe` |
| 运行输出 | 源码：`out\`；exe：exe 同级 `out\` |
| 模型缓存 | `out\llm_cache\` |
| 研究产物 | `out\study\study.png`、`out\study\study.json` |
| 标注数据 | `out\marks\marks.json`（规则正式）、`out\marks\marks_demo.json`（异常兜底） |
| 复核截图 | `out\ui\review_terse.png`、`review_coach.png`、`review_audit.png`（同名 `.txt` 为全文） |
| 标注证据图 | `out\ui\marks_preview.png`、`hud_marks.png`、`marks_export.png`、`panel_marks.png` |
| UI 预览证据 | `out\ui\overlay_preview.png`、`out\ui\panel_preview.png` |
