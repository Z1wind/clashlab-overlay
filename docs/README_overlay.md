# ClashOverlay 进程外覆盖层 · 使用说明

> 口径以代码为准：入口 `run_overlay.py` / `overlay_exe_main.py`、配置 `config/overlay.json` + `config/overlay_keys.json`、运行时 `clashlab/overlay/runtime.py`、页面 `pages.py`、键表 `keys.py`、本地引擎 `tactics.py`。
> 最后更新：2026-11-23（双引擎/可改键/输入修复轮）。

## 1. 一句话定位

在雷电模拟器窗口上方叠一层**进程外**透明覆盖层：HUD 模式只画战术标注、鼠标完全还给用户；按 `toggle_mode` 热键（默认 F8）同一个窗口变可交互面板，再按同一键或 ESC 立刻退回 HUD。注意：默认 F8 与雷电**全局**录屏钩子撞车（实测按 F8 会点亮它的「视频录制」窗），建议设置页改绑非 F 键，详见 §3 警告。

PANEL 研究页内置**双引擎**：`local` 本地规则引擎（离线、确定，读 `out/prebattle/info.json` 的 exposed 按 dps 分档配色）/ `llm` 大模型战术策略（联网、后台线程，deepseek-v4.1-flash 出三段式进攻建议）。**引擎切换只在面板点按钮，没有热键。**

**铁律：单进程、单个用户可见窗口，全程不出现第二个窗口。** 研究触发、截图选择、日志查看全部在这一个窗口内完成，禁止系统文件对话框、禁止弹窗、禁止第二实例。

技术边界：不注入 DLL、不 hook D3D/GL、不读写游戏内存、不改游戏进程；触控走 Windows 鼠标事件（SendInput 主路径，PostMessage 备选，ADB 兜底）。为什么这样选，见 `docs/injection_decision.md`。

## 2. 怎么起

### 2.1 源码运行

```powershell
cd "C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
# 可见 PANEL（单屏已自动放行；--allow-primary 为显式开关，见 §2.3）
& "D:\Python313\pythonw.exe" overlay_exe_main.py --mode PANEL
# 或业务入口 run_overlay.py（参数同名）
& "D:\Python313\python.exe" run_overlay.py --show --mode PANEL
```

参数（以 `overlay_exe_main.py` / `run_overlay.py` argparse 为准，两者同名同语义）：

| 参数 | 作用 | 默认 |
|---|---|---|
| `--root DIR` | 项目根（数据/配置相对此解析；EXE 态自动向上找根标记） | 入口所在目录 |
| `--show` / `--no-show` | `--show` 进入可见覆盖层；不带则为不可见自检模式（EXE 双击默认可见，源码默认自检） | 源码关 / 打包开 |
| `--mode HUD` / `--mode PANEL` | 启动模式 | HUD |
| `--always-on-top` | 常显（默认关闭=跟随前台，雷电不在前台即隐藏） | 关 |
| `--run-seconds N` | 可见模式运行 N 秒后自动退出（调试用） | 不退出 |
| `--seconds N` | 自检模式退出秒数 | 30（`config/overlay.json` 的 `self_check_seconds`） |
| `--allow-primary` | 显式放行开关：允许覆盖层出现在主显示器；**单显示器环境已自动放行并打 WARN**（`[WARN] single monitor: primary guard auto-relaxed`），无需带此开关；≥2 块显示器时落主屏仍由守卫拦截 abort | 关 |

`pythonw` 无控制台黑框；`--no-show` 仅 shim（`overlay_exe_main.py`）提供，强制走自检。
自检模式日志见 `out/overlay/overlay.log`，出现 `self-check mode (invisible) start/done` 即正常，不建窗。

### 2.2 打包 exe 运行

产物 `dist\ClashOverlay.exe`（PyInstaller onefile，最终构建 **88,468,375 B @2026-11-23 22:07:26**，日志 `out/overlay/build_input_fix.log`；构建脚本与口径见 `docs/packaging_check.md`）：

```powershell
.\dist\ClashOverlay.exe                      # 双击/直接启动，可见 HUD（不带参数=HUD）
.\dist\ClashOverlay.exe --mode PANEL         # 启动即面板
.\dist\ClashOverlay.exe --allow-primary      # 显式放行主屏（单屏已自动放行，仅 ≥2 屏需用，见 §2.3）
.\dist\ClashOverlay.exe --run-seconds 20     # 跑 20 秒自动退（取证用）
.\dist\ClashOverlay.exe --root DIR            # 换数据根目录
```

打包态默认可见（`--no-show` 可切自检）；默认跟随前台——雷电不在前台时窗口隐藏，切回再显；数据按 **exe 所在目录**相对解析（向上找 `config/anchors.json` / `out/prebattle` / `clashlab/geo.py` 根标记），不写死绝对路径，可整体拷贝到别处运行。

### 2.3 前置

- 雷电 LDPlayer9 实例 0 已启动、CoC 在前台或后台均可（覆盖层只贴窗口矩形，不依赖游戏画面内容）；
- 系统 DPI 100%（96）为实测环境；
- 触控真实下发另走 `clashlab/touch.py` / `clashlab/autoplay.py`，覆盖层本身不连 adb；
- **显示拓扑（随环境变化，以 `out/overlay/display_topology.json` 为准）**：实测双屏期主屏 `\\.\DISPLAY2` (0,0)-(1920,1080)（Primary）、外接屏 `\\.\DISPLAY1` (1920,0)-(3840,1080)；外接屏断开后为单主屏（`monitor_count=1`，仅 primary）。覆盖层、测试窗、截图取证只落在外接屏；**覆盖层不会出现在主屏，也不盖主屏任何窗口**。渲染面经 `ldconsole --lockwindow 1` 锁定 1280×720；运行时每帧按 `ClientToScreen`+`GetClientRect` 重测渲染客户区，具体坐标以 `overlay.log` 的 `rect sync` 行为准，不写死。
- **守卫（GUARD_PRIMARY_DISPLAY 默认开）**：target 落在 primary 时的拦截分两档——**只有 1 块显示器：自动放行并打 `[WARN] single monitor: primary guard auto-relaxed (only 1 display present)`，不再 abort**；**≥2 块显示器：落主屏仍拒绝可见，打印 `[GUARD] target on primary display`（旧口径 `only primary monitor available`）并退出**。`--allow-primary` 为显式放行开关（单屏无需带）。拓扑快照落 `out/overlay/display_topology.json`（`monitor_count`/`target_rect`/`visible_intersection_area`/`partially_offscreen`）。

### 2.4 窗口行为三条铁律

1. **覆盖层窗口严格等于雷电渲染客户区**：不铺满外接屏、不覆盖雷电外的任何区域；客户区多大，覆盖层就多大。
2. **默认跟随前台**：雷电不在前台时覆盖层自动隐藏（`SW_HIDE`），切回雷电再 `SHOWNOACTIVATE` 出现；仅 `--always-on-top` / `always_on_top=true` 常显（取证用，默认关）。
3. **只出现在外接屏（≥2 屏环境）**：跟随目标落在外接屏区域，不向主屏扩散，不遮挡主屏任何用户窗口；渲染窗在 ≥2 屏时被挪到主屏 → `[GUARD]` 守卫拒绝进入可见循环、不建窗（`--allow-primary` 显式放行）；**仅 1 块显示器时守卫自动放行打 WARN、不再拦截**。守卫提示原文（≥2 屏被拦时）：`ACTION: connect secondary display, or move LDPlayer inside visible desktop, or pass --allow-primary (not recommended).`

## 3. 热键表（可配置，改键热生效）

键表配置文件为 `config/overlay_keys.json`（不再由运行时独占写 `config/overlay.json` 的 `hotkeys`；`overlay.json` 里的 `hotkeys` 是旧展示表，运行时不认）。设置页提供改键 UI：`[改键]` 进入捕获态、`[清除]` 解绑、`[恢复默认]` 一键还原；保存即写 json，运行时按文件 mtime 热重载，**不用重启**。读文件缺失/损坏回退默认并记 warn 日志。

| 动作 id | 中文名 | 默认键 | 当前绑定（实读 json） | 说明 |
|---|---|---|---|---|
| `toggle_mode` | 切换面板 | F8 | F8 | HUD ⇄ PANEL；**⚠ 默认 F8 与雷电全局录屏钩子撞车**：实测按 F8 会被雷电吃掉、直接点亮「视频录制」窗（`LDVideoRecordWindow`，与前台无关），建议设置页改绑非 F 键（如 `tab` / `m`），或接受「切模式顺手开录屏」的代价；该场景实机复验挂起 `pending-user-gaming` |
| `capture` | 采集一帧 | F9 | F9 | 发 start/stop 采集请求（真实启停由触控线执行） |
| `live` | Live 跟随 | F7 | F7 | live / dry-run 切换，HUD 角标同步 |
| `reload` | 重载情报 | F12 | F12 | 按 mtime 侦测重读数据，不重启进程 |
| `back_hud` | 回 HUD | ESC | ESC | PANEL → HUD 恢复穿透；捕获态下 ESC 只作取消 |

引擎切换（local/llm）**不绑定热键，只在面板研究页点按钮**。

轮询：`GetAsyncKeyState` 全局边沿轮询，不要求窗口焦点；键表来自 `keys.vk_map()`，mtime 变化即重新载入。

**冲突规则**：两个动作共用同一键 → 设置页红字「已被 <动作名> 占用」拒绝写入，原绑定不变；与雷电自身占用键（F8 录屏 / F9 操作录制 / F11 全屏）撞车 → 黄字警示、允许坚持绑定，提示记入 json 的 `warnings`。**实测：默认 `toggle_mode=F8` 撞的是雷电全局录屏钩子（与前台无关），按 F8 即点亮 `LDVideoRecordWindow` 录屏窗，覆盖层拿不到干净切换动作**；首选用 `tab` / `m` 等非 F 键改绑，复验挂起 `pending-user-gaming`。

**可见性策略**：默认跟随前台——雷电不在前台时覆盖层自动隐藏（`SW_HIDE`），切回雷电再 `SHOWNOACTIVATE` 出现；PANEL 态经 `panel_keep` 抑制前台跟随隐藏；`--always-on-top` / `always_on_top=true` 才常显（仅取证用，默认 false）。

## 4. 四个页面（同一个 PANEL 窗口内切换）

PANEL 容器：右侧半透明底板（宽 `min(420, W*0.45)` 自适应）+ 顶部 **研究 / 阵型 / 采集 / 设置** 标签条，不写死像素、不开子窗、不用 Popup/Modal。

### 4.1 研究页 research（双引擎）

顶部引擎带两个按钮：**本地模式** / **大模型模式**，切换只在此点按，无热键。

- **本地模式（local）**：读 `out/prebattle/info.json` 的 `exposed`，按 dps 降序分档配色（前 3 红 rank3、4–6 橙 rank2、其余蓝 rank1）；每栋一行按钮（名称/格/dps），点选聚焦，右侧显示威胁/次要/可忽略计数；HUD 同步画聚焦框。数据源缺文件降级空壳不崩。
- **大模型模式（llm）**：先选目标（三星 / 两星 / 打资源 / 清边），点「生成策略」后台线程调 `llm.chat`（provider openai_1，模型 deepseek-v4.1-flash，timeout 40s，空 content 重试 3 次、每次 sleep 1.2s）；成功判据为 `out/overlay/tactics/plan.json` mtime 新于点击时刻且正文 >50 字，等待窗口 ~180s；三段正文（威胁排序 / 进攻路线 / 兵种与法术）折行渲染在 plan_box。

### 4.2 阵型页 layout（候选编辑器）

- 研究图/底图缩略等比 fit 居中（letterbox），候选列表按置信度降序，阈值小按钮过滤（全部 / ≥.3 / ≥.5 / ≥.7），每行选中、隐藏、删除；
- 画布点选/拖动/拖角改大小，「补框模式」空白处按下-拖出矩形建框；右键删误检；
- **冻结 layout** 按钮：绿 OK / 红 X 常驻一行提示，产物 `layouts/layout_current.json` 原子替换 + 去重时间戳快照。
- 当前 `layout_candidates.json` / `overlay.png` / `layout_current.json` 缺文件时降级空壳，不拒绝进入。

### 4.3 采集页 collect

- 只读 `out/farm/farm_report.json`：mode / live / dry-run、scouted/skipped/errors/menu_opened、blockers（红字逐条）；不实例化 Farm、不连 adb；
- 三个按钮：**开始采集** / **停止**（只发请求给运行时，动作交触控线）、**Live/Dry** 切换（同 F7，写 `state.live`）；
- `out/overlay/clicks.log` 末 20 行固定区，倒序看最近点击记录。

### 4.4 设置页 setting

- 实测锚点表：confirmed 绿字，`scout_back`/`scout_attack` 等未验证项灰字标 `[未验证]`，禁止当已确认点；
- **5 行绑键表可改**：左动作名 / 中右对齐当前键 / 右 `[改键]` `[清除]`，底部 `[恢复默认]` + 状态文字；红字=动作间冲突拒绝，黄字=与雷电自身键撞键（允许坚持，记入 warnings），绿字=已保存；
- 贴合偏移 dx/dy 数值框（保存由运行时写 config，面板不回写）；
- 模型只读（`config/ui.json` 的 `model`）。
- **pending：设置页在真实客户区 1002×563 下高度溢出，底部页脚/档位栏被切**（720×640 离屏图内容顶到 y=639）；排版待按 1002×563 收敛，证据图 `out/overlay/settings_live_1002x563.png`（待补），执行线重排中，勿写成已解决。

> 字体口径：`msyh.ttc` 纯直载（`CJK font msyh.ttc loaded (plain)`），中文正常显示，无需降级英文。

## 5. 怎么切回 dry-run

两条路，互为备份：

1. **界面/热键**：PANEL 采集页拨 live 开关，或全局按 **F7**，`state.live=False` 即 dry-run；HUD 角标显示 `live=dry`。dry-run 下触控只写日志不下发。
2. **命令行**：半自动放兵显式 `python -m clashlab.autoplay --dry-run`（`--channel auto|mouse_sendinput|mouse_postmsg|adb`、`--serial`、`--wait-ms`、`--marks` 可选），全流程只记录、0 真点；ESC 在该进程内立即置停。

## 6. 数据契约

覆盖层只读下列文件，缺文件/坏 JSON 一律降级空壳不崩；冻结产物写 `layouts/`。

| 文件 | 内容 | 消费方 |
|---|---|---|
| `out/marks/marks.json` | `marks`（目标/规避建筑）、`lines`（射线）、`pins`（入场点）、`circles`（法术半径）、`steps`（前 2 条关键步骤小字） | HUD 绘制 |
| `out/study/study.png` / `out/study/study.json` | 研究图 / 研究报告 | 研究页 |
| `out/prebattle/brief.md` / `out/prebattle/info.json` | 赛前简报 / 情报（th、防御计数、外露、盲区） | 研究页 |
| `out/overlay/layout_candidates.json` | 识别候选 `candidates[]`（bbox/confidence/tile）+ 可选 `quad` | 研究页候选表/编辑器 |
| `out/overlay/overlay.png` | 候选框已画底图（可缺，缺则原始截图占位） | 编辑器画布 |
| `layouts/layout_current.json` + `layouts/layout_<ts>.json` | 冻结当前态 + 去重快照（buildings/removed/quad/source） | 冻结产物 |
| `out/farm/farm_report.json` | farm 只读状态 | 采集页 |
| `out/overlay/clicks.log` | 全量点击记录 | 采集页尾部 |
| `config/overlay.json` | 自检秒数、fps 窗口、贴合偏移 dx/dy（旧 `hotkeys` 展示表，运行时不读） | 运行时 |
| `config/overlay_keys.json` | 5 动作键表 `keys{}` + 雷电撞键警示 `warnings{}`，设置页可写、mtime 热重载 | 运行时/设置页 |
| `out/prebattle/info.json` `exposed` | 外露建筑类型/格坐标/dps/edge_dist | 本地引擎分档 |
| `out/overlay/tactics/plan.json` | 大模型策略产物（model/elapsed/goal/sel/text），mtime 作成功判据 | 大模型模式 |
| `config/anchors.json` | 锚点覆盖表（与内置实测表合并） | 设置页 |

坐标口径：tile ↔ 渲染像素（1280×720）只走 `clashlab/geo.py` 的 `Calib` 单应矩阵，禁止自写线性插值。

## 7. 已知限制（均带触发条件）

1. **模拟器版本/分辨率未全覆盖**：仅雷电 LDPlayer9 实例 0、1280×720 横屏（adb `wm size` 物理 720×1280/density 320）实测；换版本、非 16:9、画面带黑边时「线性拉伸无黑边」假设失效，标注会错位。
2. **DPI 非 100% 未实测**：仅 96（100%）验证；系统 125%/150% 缩放下几何贴合未测，可能偏移（进程已置 Per-Monitor v2，`GetDpiForWindow` 在位）。
3. **CJK 字体已通**：`msyh.ttc` 纯直载（新 atlas 1.92 无 glyph_ranges 形参），日志 `CJK font msyh.ttc loaded (plain)`；`cjk_proof.png`（997×561）中文标签与步骤行单层清晰，非 `???`。
4. **PANEL 焦点与输入法**：`WM_IME_*` 不转发，面板无中文输入框，label 用点选/粘贴；面板默认不抢焦点、全鼠标操作；临时焦点原语（request_focus/release_focus）在位但不主动用。
5. **单指针，同点多兵做不到**：Windows 鼠标单指针，RenderWindow 不产生第二指针，并发批=1；同时下多兵需 minitouch（未安装，不纳入本版）。
6. **多开仅实例 0**：运行时取第一个可见 `LDPlayerMainFrame`，第二实例未测、未寻址。
7. **穿透证据分层**：静态 `WindowFromPoint` 命中测试 9/9 放行已证；`pm_click.json`（19:37:08）WS_EX_NOACTIVATE+PostMessage 闭环、目标自回 `CLICK RECEIVED @5400,490`、fg_before==after=0x1600bc 已证；游戏锚点 PostMessage battle/build 各 20/20、前台恒定已证；但「点击穿透覆盖层后激活非目标其他窗口」的对照仍未取证。
8. **动态贴合连拍待显示器条件**：`fit_move/resize/fullscreen.json` 现标 `pending-external-display`，等待条件 `monitor_count≥2 且 target monitor 非 primary`（单屏已自动放行，不再以守卫 abort 为由禁止验证，但连拍采样仍需 ≥2 屏环境）。旧 997×561 几何下的 offset=0 数字随几何变更作废，不沿用；待条件满足重跑 `fit_probe.py` move/resize 采样，全屏项预期 rect sync -> client=(x,y,1920,1080) 且与客户区一致。
9. **FPS 数值口径**：新 60fps 显式 pacing（每帧 sleep 到下一帧时点），仅统计可见绘制帧；HUD mean 60.05 / PANEL mean 59.6，帧时间 p50≈16.7ms，min 出现在启动/模式切换边界帧，不代表稳态；旧忙等迭代数（639.89/10413/691）作废。具体数字见 `docs/overlay_evidence.md`，随每次运行重写。
10. **首击恢复已取证**：restore→hit **4.31ms**（≤16.7ms 达标，`first_click.json` 19:38:40）；switch→hit 89.94ms 含 60ms ESC 按键保持，不是恢复耗时，不混写。
11. **候选/编辑器数据当前缺文件**：`layout_candidates.json`、`overlay.png`、`layout_current.json` 现阶段不存在，研究页候选区与编辑器降级空壳，待识别线/冻结产物落盘。
12. **标定绑定雷电渲染客户区，位置强耦合**：覆盖层矩形每帧跟随 `RenderWindow/TheRender` 客户区；若雷电被拖到主屏、被移出外接屏范围，或多开实例出现在别处，覆盖层会跟错目标，需要重新标定。检查方法：`overlay.log` 的 `overlay rect sync -> client=(x,y,w,h)` 与雷电实际客户区对照；轻量修正：设置页 dx/dy 偏移微调 + 重启覆盖层重贴；注意外部 `MoveWindow` 改不动渲染面（位置/尺寸由模拟器自决），改分辨率/锁定尺寸需 `ldconsole modify --index 0 --resolution ... --lockwindow 1` 后重启实例。当前几何：客户区 962×541 @ (2101,146)，sx=0.75156/sy=0.75139（`borders.json` 19:54:15）；旧 997×561（sx 0.77891/sy 0.77917）为历史口径已作废。行为承诺：覆盖层只绘制在跟随目标的外接屏区域内，不会跑到主屏遮挡用户窗口。
13. **PANEL 输入法/中文输入限制**：`WM_IME_*` 不转发，面板无中文输入框，候选 label 走点选/粘贴，不在面板敲中文；中文显示已由 msyh.ttc 直载解决（`cjk_proof.png` 样张）。
14. **窗口尺寸由模拟器锁定**：渲染面 1280×720 1:1 经 `ldconsole --lockwindow 1` 落地；解除锁定或换分辨率前，不要期望外部移动/缩放窗口能改变渲染面。
15. **离屏渲染图不能作文字可读性证据**：`tools\panel_render_check.py` 以 `glfw.VISIBLE=FALSE` 不可见上下文离屏渲染，只验证布局（叠字/裁切/形状/条带在框内），不得据此判中文清晰；文字可读性以可见态截图为准。
16. **不做截图模板 CV 识别建筑类型**：这条路已证死——tile_px 22/25/28 三档实测 eagle 最高 0.584、p99 0.473，inferno 仅 0.348，与背景不可分；颜色+形状分割只出 3 连通块。类型只能来自 `out/prebattle` 既有情报，本层只承诺「位置 + dps 威胁排序」。
17. **DPS 来自 `out/prebattle/info.json`，不是战斗实时抓取**：阵型变了不会自动更新，需重跑分析后按 F12 重载。
18. **实机大尺寸（1600×900 / 1920×1080）未实测**，待接外接屏再验；目前只有离屏证据 `out/overlay/mode_local_1080.png`，不写实机大尺寸结论。
19. **PANEL 不抢前台**：Windows 前台锁下 `SetForegroundWindow` 可能被拒，运行时刻意不调；鼠标输入走帧级自喂（`GetCursorPos` + `GetAsyncKeyState(VK_LBUTTON/RBUTTON)` 边沿喂 imgui），不依赖窗口焦点，也不把雷电挤到后台。
20. **默认 `toggle_mode=F8` 与雷电全局录屏钩子撞车**：F8 是雷电全局钩子（与前台无关），实测按 F8 会被雷电吃掉、直接点亮「视频录制」窗 `LDVideoRecordWindow`，覆盖层拿不到干净切换动作。建议设置页改绑非 F 键（`tab` / `m`），或接受「切模式顺手开录屏」的代价；该场景实机复验挂起 `pending-user-gaming`。

## 8. 排错

| 现象 | 先查 | 怎么修 |
|---|---|---|
| 覆盖层没出来 | `out/overlay/overlay.log`：有 `self-check mode` 说明走了自检（`show=false`）→ 加 `--show`；有 `overlay runtime start` 无 `window visible` → 看其后 GL/backend 报错；`--run-seconds` 到点会正常退出 | 自检模式本就不建窗；可见模式报错按终端/日志堆栈补依赖 |
| 贴合偏了 | `overlay.log` 的 `overlay rect sync -> client=(x,y,w,h)` 与雷电实际客户区是否一致；`config/overlay.json` 的 `offset.dx/dy` | 设置页数值框微调偏移；确认窗口没被拖出外接屏，每帧 ClientToScreen+GetClientRect 跟随在位（移动/缩放/全屏连拍 offset=0 已取证）；先重启覆盖层重贴 |
| 点不中/点被拦 | HUD 应穿透：对照 `passthrough.log` 口径查 exstyle 是否带 `TRANSPARENT`；`clicks.log` 的 `method_tried/errors` 看降级链卡在哪一跳 | SendInput 走前台合成；PostMessage 仅入队、免前台但游戏响应约 0.6–0.7s；ADB 兜底慢但确定；早期 8ms 零保持出现 2/20 漏发，生产 `hold_ms=30` 必须保留 |
| 中文变方块 | `overlay.log` 出现 `CJK font fallback to default` 即字体回退默认（旧运行残留）；正常应为 `CJK font msyh.ttc loaded (plain)` | 确认日志行为 loaded；若仍方块，检查 `C:\Windows\Fonts\msyh.ttc` 是否存在、重启覆盖层 |
| 游戏掉线/adb 掉 | 覆盖层不连 adb、不崩；触控侧查 `clicks.log` errors 与 `adb devices` | 坏 serial/设备消失时 `_adb_tap` 返回 `(False, err)` 不抛栈；`python -m clashlab.autoplay --dry-run` 先空跑验证流程，再 live |

## 附：关键路径

| 用途 | 路径（相对项目根） |
|---|---|
| 入口 | `run_overlay.py`（业务）/ `overlay_exe_main.py`（EXE shim） |
| 运行时主循环 | `clashlab/overlay/runtime.py` |
| 数据层/编辑器/页面骨架 | `clashlab/overlay/data.py` / `editor.py` / `pages.py` |
| 配置 | `config/overlay.json`、`config/overlay_keys.json`、`config/anchors.json`、`config/ui.json` |
| 运行日志 | `out/overlay/overlay.log` |
| 触控报告与取证 | `out/overlay/touch_report.md`、`fps_summary.json`、`passthrough.log`、`measure_out.jsonl` |
| 打包脚本 | `build_overlay.ps1`；产物 `dist/ClashOverlay.exe`（构建日志 `out/overlay/build_input_fix.log`） |

---

**打包状态**：`dist/ClashOverlay.exe` 最终件 88,468,375 B @22:07:26（BUILD OK 34.9s），含单屏放行、设置页修复、按钮 ID 修复，包码同步；后续重建与试跑口径以打包线为准。
