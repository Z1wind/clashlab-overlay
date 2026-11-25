# 打包试跑核对记录（ClashOverlay.exe）

> 最终重建：2026-11-23 20:21（UTC+8，含 pages.py 配色定稿 20:17:06）；试跑 20:21:20–20:21:32。
> 脚本：`build_overlay.ps1`（项目根，可重复执行，先清 `build\` 与旧 exe）；产物：`dist\ClashOverlay.exe`。
> shim `overlay_exe_main.py` 仅解 exe 相对根目录与参数；`clashlab\overlay\pages.py`（20:17:06 定稿）由 PyInstaller 从项目根收集，随本版打入。

## 1. 环境

| 项 | 值 |
|---|---|
| Python | 3.13.5（`D:\Python313\python.exe`） |
| PyInstaller | 6.22.3（hooks-contrib 2026.10） |
| 关键依赖 | imgui_bundle 1.93.0（cp313 wheel）、PyOpenGL 3.1.10、glfw 2.11.0、pywin32 312、numpy 2.5.5、opencv 5.1.0.95 |
| 入口 | `overlay_exe_main.py`（打包 shim，仅解 exe 相对根目录与参数；业务入口仍是 `run_overlay.py`，未改） |

## 2. 构建过程与失败修复

| 轮次 | 结果 | 说明 |
|---|---|---|
| 第 1 次 | BUILD OK，87,837,875 字节 | 警告 `Library glfw3.dll required via ctypes not found`：glfw 经 ctypes 动态加载，静态分析收集不到，运行时可能缺 DLL |
| 修复 | 脚本加 `--collect-binaries glfw --collect-binaries imgui_bundle` | 不改动任何业务代码 |
| 第 2 次起 | BUILD OK | glfw3.dll 警告消除；`MSVCR90.dll` 警告为未使用的 freeglut/gle 旧 DLL 依赖，忽略 |
| **冻结前最近一次构建（20:21 轮，非终版）** | 88,446,794 字节（≈84.35 MiB），墙钟 33.4 s | 含 shim `--always-on-top` 透传；该轮 pages.py 早于 MainAgent 引擎双模式，**解冻后须重建**，此体积/耗时不作终版口径 |

构建墙钟 33.4 s（脚本内 Stopwatch 实测，20:21 轮）；脚本可重复执行。**PACKAGING_HOLD：pages.py 双模式未冻结前不再重建。**

## 3. 启动验证（最终重建）

### 3.1 自检模式（`--no-show --seconds 2`，20:21:20 最终轮）

- 进程 exit_code=0；未建窗；`dist\out\overlay\overlay.log` 记录 `self-check done in 2.0s (no window shown)`；
- 日志落在 exe 同级 `dist\out\`，证明打包后按 exe 所在目录相对解析，无绝对路径写死。

### 3.2 本轮可见试跑：守卫 abort（20:21:32，打包产物同样受保护）

- 环境：外接屏物理断开，`monitor_count=1`（仅 primary 0,0,1920,1080），RenderWindow (2101,146,3063,687) `visible_intersection=0`、`partially_offscreen=true`（`display_topology.json` 19:58:17）。
- 打包 exe `--always-on-top` 启动：进程 5s 内自行退出，枚举 **零 `clashlab-overlay` 窗口**；
- `dist/out/overlay/overlay.log` 20:21:32 记录：
  - `[GUARD] partially-offscreen=true target_rect=(2101,146,3063,687) visible_intersection=0 < target_area=520442`
  - `[GUARD] only primary monitor available; monitors=1 (no secondary). target_rect=(2101,146,3063,687) visible desktop=(0, 0, 1920, 1080). ACTION: connect secondary display, or move LDPlayer inside visible desktop, or pass --allow-primary (not recommended).`
- 结论：**abort/不建窗是本轮正确期望**，证明打包产物与源码运行同样受守卫保护；count=1 + rect 全等复验待显示器条件恢复（monitor_count≥2 或 target 落可视区）后补做。

### 3.3 双屏历史试跑（19:49:56，外接屏在位，留档）

- 枚举 **count=1**：`0x2075c`，GLFW30，标题 `clashlab-overlay`，visible=true；rect 与 RenderWindow 客户区全等（dx/dy=0）；fg_before==after=0x1600bc（雷电模拟器），`fg_preserved=true`，未抢焦点；到时干净退出。
- 该次为外接屏在位环境，现单主屏环境不复现，数字仅留档（`final_trial.json` 19:50:01）。

### 3.4 PANEL 启动（前次重建试跑，`--mode PANEL --run-seconds 12`）

- 日志：`start_mode=PANEL; always_on_top=False` → `rect sync` → `HUD->PANEL (TRANSPARENT removed)`；
- **无** `pages.draw_panel error`（旧版 `WINDOW_NO_TITLE_BAR` AttributeError 已随面板线重写消除）；
- 跟随前台策略下雷电不在前台时窗口 `SW_HIDE`，枚举为 0 属正常行为，非故障。
- 注：本轮 pages.py 配色定稿（正文纯白、底板 (0.035,0.055,0.095,0.92)、边框提亮、缺底图 quad 菱形+淡网格+原点十字、候选框序号气泡）；PANEL 实窗可见态截图待显示器条件恢复后补拍，离屏图不作可读性证据（见证据表 §2.2）。

### 3.5 PANEL 启动（前次重建试跑，`--mode PANEL --run-seconds 12`）

- 日志：`start_mode=PANEL; always_on_top=False` → `rect sync` → `HUD->PANEL (TRANSPARENT removed)`；
- **无** `pages.draw_panel error`（旧版 `WINDOW_NO_TITLE_BAR` AttributeError 已随面板线重写消除）；
- 跟随前台策略下雷电不在前台时窗口 `SW_HIDE`，枚举为 0 属正常行为，非故障。

## 4. HUD/PANEL 正常性口径

- HUD 绘制（marks 散点/黄菱形 pin/绿圆/橙目标环/右上 live 角标）与 F8/ESC 同帧切换的证据来自源码运行（`final_hud.png`、`final_panel.png`、`overlay.log` F8/ESC 行、`runtime_route.md`）；
- 打包试跑验证：exe 能起、自检干净（20:21:20 exit=0）、守卫在打包产物上同样 abort（3.2）；双屏环境历史单窗口 count=1/前台不抢见 3.3；**打包产物上的目视绘图复核未做**，列入开放项。

## 5. 复核记录（收尾逐条回源，已闭环）

| 写作时的不确定项 | 回源结果 | 结论 |
|---|---|---|
| FPS 旧值 639.89/10413/691 | `fps_summary.json`（19:37:44）新 60fps pacing 口径，旧忙等迭代数作废并标 `deprecated_note` | 已替换，证据表采用新口径 |
| 可见窗口数 | `enum_windows.json`（18:47:19）count=1；最终试跑 `final_trial.json`（19:50:01）count=1、rect 全等、fg 保持 | 已取证 |
| CJK 字体是否仍 tofu | `msyh.ttc loaded (plain)`；`cjk_proof.png` 997×561 中文清晰 | 已闭环 |
| PANEL `WINDOW_NO_TITLE_BAR` 报错 | 面板线重写 pages.py，试跑无该错误 | 已消除 |
| 黑边/缩放系数（新几何） | `borders.json`（19:54:15）客户区 962×541 @(2101,146)、sx=0.75156/sy=0.75139、黑边 0/0/0/0、边带 RGB 12.8–83.1 非纯黑；旧 997×561（sx 0.77891/sy 0.77917）标历史口径作废 | 已入证据表 |
| 首击恢复 | `first_click.json`（19:38:40）restore→hit 4.31ms；switch→hit 89.94ms 含 60ms ESC 保持，不混写 | 已入证据表 |
| 动态贴合连拍 | `fit_move/resize/fullscreen.json` 现标 `pending-external-display`（等待 monitor_count≥2 且 target 非 primary）；旧几何 offset=0 作废不沿用 | 已入证据表 |
| 守卫 abort（打包产物） | 20:21:32 打包 exe 单主屏 + off-screen 下 `[GUARD] only primary monitor available; monitors=1...` 拒绝建窗、进程退出、零窗口 | 已入 §3.2 |
| 离屏渲染取证限制 | `panel_render_check.py` 不可见上下文采不到字体图集纹理（可见 luma=255 vs 离屏 ~27），离屏图只验布局、不验文字 | 已入证据表 §2.2 |
| PostMessage 通道 | `postmsg_success.jsonl` battle/build 各 20/20、fg 恒定；入队 0.122/P95 0.302ms；20 连击 5.64ms | 已入证据表 |
| 穿透不抢前台 | `pm_click.json`（19:37:08）fg_before==after=0x1600bc，fg_preserved=true | 已入证据表 |

## 6. 开放项（不属本次可闭环，移交对应线）

| 开放项 | 归属 | 状态 |
|---|---|---|
| 20 连击游戏侧处理数回读：无回读接口，仅下发侧 20/20 | 游戏侧 / 不补 | **无法核实**，保持口径 |
| `passthrough_groupA.png`/`groupB.png` 1920×1080 单屏整幅 → 外接屏裁切版重拍 | 运行时线 | **待重拍** |
| PANEL 实窗可见态截图 | 运行时线 / 待显示器条件 | **待条件**（单主屏守卫 abort，无可见窗可拍；离屏图不作可读性证据） |
| 打包产物上目视复核 HUD 绘图与 PANEL 容器 | 交付后人工 | 待人工 |

> **PACKAGING_HOLD: waiting for MainAgent to finish pages.py dual-mode** —— pages.py 引擎双模式（research 本地/大模型、PAGE_LAYOUT 页、顶部模式带、STACK_TOP 84→112）未冻结前，暂停重建 `dist\ClashOverlay.exe`；`overlay_exe_main.py` / `build_overlay.ps1` 打包逻辑不动、保留可用。解冻后一次性完成：重建 exe（体积/耗时）、试跑（守卫 abort 或 count=1 视环境）、四份文档终稿、待复核项清零（仅留三条不可闭环）。
