# 覆盖层取证数字表

> 口径：每个数字都抄自 `out/overlay/` 实际产物，注明来源文件与记录时间；抄不到写「未取证」并列缺哪个文件。
> 汇总时间：2026-11-23 19:50（UTC+8，含最终打包试跑）。采样环境：雷电 LDPlayer9 实例 0，系统 DPI 96；渲染面经 `ldconsole --lockwindow 1` 锁定为 1280×720。

## 1. 总表（主口径）

| # | 指标 | 数值 | 来源文件 | 记录时间 |
|---|---|---|---|---|
| 1 | 黑边（四边纯黑判定，40px 条带 RGB 均值<12） | **0 / 0 / 0 / 0**（四边均 >12，无纯黑边；边 1px 为 PrintWindow 边框伪影按 0） | `out/overlay/borders.json`（`black_px`） | 19:54:15 |
| 1 | 缩放系数（当前几何 v2） | sx=962/1280=**0.75156**，sy=541/720=**0.75139**；客户区 **962×541 @ (2101,146)**，aspect 962/541=1.7782 vs 1280/720=1.7778 | `borders.json`（`scale`/`render_client_rect`） | 19:54:15 |
| 1 | 边带非纯黑自证 | 四边 40px 条带 RGB 均值落在 **12.8–83.1**（max 246–255），非纯黑 | `borders.json`（`samples`） | 19:54:15 |
| 1 | 旧几何（历史口径，已作废） | 997×561 @ (2363,276)，sx=0.77891 / sy=0.77917，黑边上0/下1/左0/右0；实例 0 以 `--resolution 1280,720 --lockwindow 1` 重启后不再适用，不沿用 | `borders.json`（`previous_geometry_deprecated`） | 19:54:15 |
| 2 | 动态贴合 · 移动 | **pending-external-display**：单主屏/外接屏断开环境守卫 abort，未采样；待 `monitor_count≥2 且 target monitor 非 primary` 后重跑 `fit_probe.py` move；旧几何 offset 数字作废不沿用 | `out/overlay/fit_move.json` | 19:58:23 |
| 2 | 动态贴合 · 缩放 | **pending-external-display**，同上待条件 | `out/overlay/fit_resize.json` | 19:58:25 |
| 2 | 动态贴合 · 父框置全屏矩形 | **pending-external-display**，同上待条件（预期 overlay rect sync -> client=(x,y,1920,1080)、与客户区一致、offset≤2px，退出全屏回落再记一行） | `out/overlay/fit_fullscreen.json` | 19:58:26 |
| 2 | 旧动态贴合口径（历史，作废） | 旧 997×561 几何下移动/缩放/全屏各 8 采样全 0、offset_max=0/avg=0px；几何已变，数字不沿用 | 旧 `fit_*.json`（已被 pending 版覆盖） | 19:35–19:36 |
| 3 | 落点几何残差（mapcheck_v2，当前几何） | 最大 **0.188 px**（底边中点），中心 0.094px，四角 0；<2px 门槛 | `out/overlay/touch_report.md` §2 | 19:3x |
| 4 | 可见窗口数（源码运行） | **count=1**：GLFW30、标题 `clashlab-overlay`、visible=true | `out/overlay/enum_windows.json` | 18:47:19 |
| 4 | 可见窗口数（双屏历史打包试跑） | **count=1**：`0x2075c` GLFW30 标题 `clashlab-overlay` visible=true，rect 与 RenderWindow 客户区全等 dx/dy=0；fg_before==fg_after=0x1600bc（雷电模拟器），`fg_preserved=true`。注：该次为外接屏在位环境，现单主屏环境不再复现 | `out/overlay/final_trial.json`；`enum_packaged.json` | 19:50:01 |
| 4b | 守卫 abort（打包产物同样受保护） | 单显示器 + RenderWindow off-screen 时 `[GUARD] only primary monitor available; monitors=1 (no secondary)...` 拒绝进入可见循环、进程退出、**零窗口**；打包 exe 实测同守卫 | `dist/out/overlay/overlay.log` 20:21:32；`guard_actionable.log` 19:58:17 | 20:21:32 |
| 4c | 显示拓扑 | `monitor_count=1`，仅 primary (0,0,1920,1080)；target (2101,146,3063,687) visible_intersection=0、partially_offscreen=true | `out/overlay/display_topology.json` | 19:58:17 |
| 5 | 帧率 · HUD（新 60fps pacing 口径） | 35s / 2097 帧：mean **60.05** / P1 54.3 / min 28.55；帧时间 p50 16.665ms / p99 18.416ms | `out/overlay/fps_summary.json`（groups.HUD） | 19:37:44 |
| 5 | 帧率 · PANEL（新口径） | 36s / 2132 帧：mean **59.6** / P1 50.06 / min 19.37；帧时间 p50 16.735ms / p99 19.977ms | `fps_summary.json`（groups.PANEL） | 19:37:44 |
| 5 | 旧 FPS 口径 | **639.89 / 10413 / 691 fps 全部作废，无效口径**（忙等自旋迭代数，非呈现帧率） | `fps_summary.json`（`deprecated_note`）；`runtime_route.md` §8.1 | 19:37:44 |
| 6 | 首击恢复（验收口径 恢复→首击） | **restore→hit 4.31 ms**（≤16.7ms 达标，`within_16_7ms_restore_to_hit=true`） | `out/overlay/first_click.json` | 19:38:40 |
| 6 | 首击恢复 · 备注 | switch→hit 89.94ms 含 60ms ESC 按键保持与轮询采样，**不是恢复耗时，不混写** | `first_click.json`（`metric_note`） | 19:38:40 |
| 7 | 静态命中测试穿透 | **9/9 通过，0 阻塞**（两轮：TkChild/Static 底、`TheRender`/RenderWindow 底） | `out/overlay/passthrough.log` | 18:04:33 |
| 8 | 不抢前台穿透（PostMessage 闭环） | 目标窗 `WS_EX_NOACTIVATE` + `PostMessage(WM_LBUTTONDOWN/UP)`，目标自回 `CLICK RECEIVED @5400,490`；`fg_before==fg_after=0x1600bc（雷电模拟器）`，`fg_preserved=true` | `out/overlay/pm_click.json`；`click_target.log` | 19:37:08 |
| 9 | 触控主通道 PostMessage · 20 连击 | battle **20/20**、build **20/20**，两批 `fg_preserved:true` | `out/overlay/postmsg_success.jsonl`；`touch_report.md` §3 | 19:04:38 |
| 9 | PostMessage 入队延迟 | 均值 **0.122 ms** / P95 **0.302 ms**（纯入队，非投递完成） | `measure_out.jsonl`（latency_postmsg_enqueue） | 18:53:35 |
| 9 | PostMessage 20 连击墙钟 | **5.64 ms**（0.28ms/call，纯入队口径） | `measure_out.jsonl`（burst20_postmsg） | 18:53:35 |
| 10 | CJK 字体与样张 | `msyh.ttc loaded (plain)`；`cjk_proof.png` 997×561 中文单层清晰（研究/采集/设置 + 中文步骤行），非 `???` | `cjk_proof.png`；`runtime_route.md` §8.2 | 19:08:51 |

## 1.1 附录对照（SendInput / ADB 为对照通道，非生产主通道）

| # | 指标 | 数值 | 来源文件 | 时间 |
|---|---|---|---|---|
| A1 | SendInput 单击延迟 n=30 两遍 | 9.18（P95 12.45）/ 11.52（P95 16.68）ms；min 2.57/7.25，max 12.91/19.67；**需前台** | `measure_out.jsonl`；`touch_report.md` §4 | 18:19:35 |
| A2 | ADB 单击延迟 n=30 两遍 | 221.70（P95 244.50）/ 224.30（P95 251.85）ms；**慢，仅兜底** | 同上 | 同上 |
| A3 | 20 连击吞吐对照 | SendInput 666.58ms（33.32/call）vs ADB 4122.19ms（206.11/call） | `measure_out.jsonl`（burst20）；`touch_report.md` §7 | 18:19:35 |
| A4 | 旧几何 mapcheck 残差 | 0.707px（旧主屏会话几何，附录 A，非当前口径） | `touch_report.md` 附录 A | 18:31:13 |
| A5 | 历史静态骨架口径 | max 1.5 / avg 0.917px（旧单屏静态测量，仅作历史口径，不用于验收） | `skeleton_layered.png.measure.json` | 17:58:21 |

## 2. 未取证项与缺文件清单（待复核项）

| 待复核项 | 状态 | 原因 / 补救 |
|---|---|---|
| 20 连击游戏侧处理数回读 | **无法核实**：游戏侧无回读接口，仅能取证下发侧 20/20 | 保持口径，不补 |
| `passthrough_groupA.png`/`groupB.png` 为单屏整幅（1920×1080），非外接屏裁切 | **待重拍** | 需外接屏 `(1920,0,3840,1080)` 裁切版穿透对照图；整幅不采信 |
| PANEL 实窗截图（可见态） | **已补**：`mode_panel_live.png`（PANEL 态）/ `mode_hud_live.png`（HUD 穿透态），见 §4.3；实机大尺寸（1600×900/1920×1080）仍待外接屏 | 离屏图不能替代，见 §2.2 |
| 旧 `passthrough_proof.png` 3840×1080 双屏整幅 | 已作废，不采信 | 不补 |

> 已核对关闭：`final_hud.png`/`final_panel.png` 为渲染子窗裁切（可采信）；`touch_proof_postmsg_battle_before/after.png` 为 1280×720 adb 游戏帧（可采信）；均非整屏，无需重拍。

## 2.2 取证能力限制：离屏渲染图不能作文字可读性证据

- `tools\panel_render_check.py` 用 `glfw.VISIBLE=FALSE` 不可见窗口上下文离屏渲染并 `glReadPixels` 读回；该上下文中**采不到字体图集纹理**：同一 Probe 白字，可见上下文纯白 luma=255，离屏仅约 27。
- 因此 `panel_offscreen.png` 只能验证**布局**（叠字/裁切/形状/条带在框内），**不能作为文字可读性证据**，不得据此判中文显示清晰。
- 文字可读性以可见态截图 `out\overlay\cjk_proof.png`（`msyh.ttc` 直载、中文单层清晰）为准；PANEL 实窗可见态截图待显示器条件恢复后补拍（列入待复核）。

## 2.1 截图证据采信规则（双屏）

- 所有截图类证据**仅采信外接屏裁切区域 `(1920,0,3840,1080)`**；整屏截图（含主屏 0–1919 列或单屏整幅）一律不采信。
- 穿透证明必填项：取证前后前台窗口标题与句柄记录不变（见 #8 `fg_before/fg_after`、#9 `fg_preserved`）；缺前台对照的静态截图不作穿透证据。
- `touch_proof_postmsg_battle_before/after.png` 为 1280×720 adb 游戏帧（非桌面屏），可采信为游戏内前后对照；`final_hud.png`/`final_panel.png` 997×561 渲染子窗裁切可采信。

## 3. 口径备注

- 新 FPS 口径：60fps 显式 pacing（每帧 sleep 到下一帧时点；swap_interval 在本机 DWM 不封顶，弃用）；仅统计可见绘制帧，隐藏帧不计；fps=1/帧间隔。min 出现在启动/模式切换边界帧，不代表稳态。
- PostMessage 0.122ms 是入队耗时，不是投递完成；游戏响应 e2e 约 0.6–0.7s 属应用处理，不计入通道延迟。
- SendInput 需前台合成，ADB 含 adb-server 往返且慢；生产主通道为 PostMessage（免前台、不抢焦点）。
- 落点误差以窗口几何投影残差为实测上界（游戏侧无真实触点回读接口）；当前几何无系统性偏移。
- 早期零保持 2/20、18/20 探针已由生产 `hold_ms=30` 规避，仅登记不并入成功率口径。

## 4. 本轮新增证据（2026-11-23 晚，单屏 `--allow-primary` 会话；数字抄自实际产物）

### 4.1 关闭雷电录屏浮窗

| 文件 | 记录 |
|---|---|
| `out/overlay/rec_off_before.png` | 关闭前：浮窗原矩形 (1400,220)-(1920,580) |
| `out/overlay/rec_off_after.png` | 雷电主窗整窗裁切 (200,150)-(1240,770)，1040×620，画面为游戏本体、无浮窗 |
| `out/overlay/rec_closed.json` | verdict `PANEL_CLOSED`：`LDVideoRecordWindow_visible_count=0`、旧 hwnd `IsWindow=false`；同区 dark_card_ratio 0.90057→0.01633、blue_button_ratio 0.0292→0.00077、MAD=193.848（阈值 60）；video3.mp4 两次读 254,062,760 B / mtime 19:59:38 未变（12s 间隔 equal=true，录制已停） |
| `out/overlay/records_moved.json` | video1.mp4 34,477,991 B、video2.mp4 3,149,927 B、video3.mp4 254,062,760 B、videorecords.xml.bak 362 B 均已移 `out/_trash/records`，pre/post 字节一致、locked=false（xml 仅复制、原件保留） |

### 4.2 双模式离屏排版（`tools/panel_render_check.py`，仅布局证据，不作文字可读性证据）

| 文件 | 记录 |
|---|---|
| `out/overlay/mode_local_720.png` | 研究页本地模式，1280×720 离屏 |
| `out/overlay/mode_llm_720.png` | 研究页大模型模式，1280×720 离屏 |
| `out/overlay/mode_layout_720.png` | 阵型页编辑器，1280×720 离屏 |
| `out/overlay/mode_local_1080.png` | 本地模式 1920×1080 离屏（**仅离屏证据，非实机大尺寸验证**） |

### 4.3 实机会话

| 文件 | 记录 |
|---|---|
| `out/overlay/mode_panel_live.png` | 实机 PANEL 态截图 |
| `out/overlay/mode_hud_live.png` | 实机 HUD 穿透态截图 |
| `out/overlay/fps_panel.json` | 2868 帧：HUD mean 60.03（1628 帧）/ PANEL mean 59.7（1240 帧）；p99 帧时间 18.294 / 19.483ms |
| `out/overlay/fps_hud.json` | HUD 单组 2097 帧 mean 60.05 / p99 18.416ms |

### 4.4 输入修复四步（面板点击链路）

| 文件 | 记录 |
|---|---|
| `out/overlay/fix_01_mode.png` | ①面板引擎按钮点击切换（local⇄llm 无热键，只走按钮） |
| `out/overlay/fix_02_plan.png` | ②生成策略后 `tactics/plan.json` 正文出现（见下） |
| `out/overlay/fix_03_select.png` | ③本地模式建筑行点选聚焦同步（`local: 聚焦 …` 日志行） |
| `out/overlay/fix_04_hud_passthrough.png` | ④切回 HUD 穿透恢复 |
| `out/overlay/input_fix_design.md` | 接手规格：根因链 / exstyle 矩阵 / 180s mtime 成功判据 |
| `out/overlay/input_fix_report.md` | **输入修复验收报告（P0 收口）**：根因=GLFW mouse_callback 仅 FOCUSED 喂光标、前台锁下 `io.mouse_pos=(-1,-1)`；修复=摘 TRANSPARENT|NOACTIVATE、不调 SetForegroundWindow、帧级自喂鼠标；exstyle 前后 hex 矩阵（HUD `0x080800a8` / PANEL `0x000c0098`）；cycle 1..11 断言全 OK 无 MISMATCH；20:38 批对账（4 保留 2 替换）；6 栋逐行命中表（6/6）；FPS 三会话；EXE §5 验收 |
| `out/overlay/tactics/plan.json` | 21:10:26，elapsed 18.25s，goal=三星，sel=鹰炮，model=deepseek-v4.1-flash，ok=true，三段正文完整 |

### 4.5 绑键

| 文件 | 记录 |
|---|---|
| `out/overlay/settings_720.png` | 设置页绑键排版（1280×720 离屏，已重出：h=640 全显、右缘留白 ≥8px） |
| `out/overlay/settings_capture.png` | 改键主链路取证：capture 改 F6，F6 生效 / 原 F9 失效（其余动作未逐个实测） |
| `out/overlay/settings_conflict.png` | 动作间同键冲突红字拒绝取证 |
| `out/overlay/keys_report.md` | **键位设置验收报告**：动作表 + VK（toggle_mode F8/0x77、capture F9/0x78、live F7/0x76、reload F12/0x7B、back_hud ESC/0x1B）；主链路 capture→F6（set_key 落盘→热重载 F6 生效→F9 delta=0 脱钩→reset 恢复）；JSON 持久化内容（version=1，五键默认，warnings={}）；F10 已彻底移除 |
| `config/overlay_keys.json` | 当前绑定实值（keys / warnings；本轮 5 键与默认一致） |

### 4.6 tactics.py 清理回归（`out/overlay/tactics_clean/`）

| 文件 | 记录 |
|---|---|
| `tactics_clean/check.log` | 仅删 `import traceback`、未引用 `COLOR_DIM` 两个死符号；保留主路径 AST 核对在；6 栋 load_local 实读核对一致 |
| `tactics_clean/mode_local_720.png` / `mode_llm_720.png` / `mode_layout_720.png` / `mode_local_1080.png` | 清理后重跑 vs 基线全部 diff_px=0（1280×720 为 0/921600，1080 为 0/2073600），字节同基线 |

### 4.7 UX 走查（22:05–22:12，用户在场）

| 文件 | 记录 |
|---|---|
| `out/overlay/exe_noarg_hud.png` | 裸双击 HUD：6 个编号圆点 + 鹰炮350 标注在屏（exstyle `0x80c00b8`，fg=LDPlayerMainFrame） |
| `out/overlay/ux_hotkey_fix.png` | 热键实测：F8→PANEL 后面板在屏（22:00:10 `-> HUD` / 22:00:24 `-> PANEL` 双向往返日志 + exstyle 双态互证） |
| `out/overlay/ux_fail_fg.png` | 雷电不在前台 → HUD 隐藏、无鬼影 |
| `out/overlay/ux_fail_llm.png` | LLM 拒连半人话：前缀可读、尾部糊 `<urlopen error WinError 10061>` |
| `out/overlay/user_experience.md` | 走查记录：裸双击勉强（空 %TEMP% 找不到数据根、静默空壳，头号分发缺口）；F8/ESC/F6 三键实测能跑；LLM 失败半人话；最少修复清单 6 条 |
| `out/overlay/final_status.md` | 22:12 收口：能用/不能用清单、包码同步、未完成项 4 条（清除/恢复默认未单点、1920×1080 未实测、LLM 空 content 未测、F8 注入点亮录屏窗未从代码规避） |

### 4.8 打包

| 文件 | 记录 |
|---|---|
| `dist/ClashOverlay.exe` | PyInstaller onefile，**最终 88,468,375 B @2026-11-23 22:07:26**（BUILD OK 34.9s；旧包 88,469,883 B @21:49:03 已被替换；对应代码 `pages.py`@22:04:55（P1 分行不裁字 + 按钮 `##aid` 唯一 ID 修 imgui 冲突弹窗）、`runtime.py`@21:48:18（单屏自动放行+WARN）） |
| `out/overlay/build_input_fix.log` | 本轮打包日志（追加至终件；终件 BUILD OK 34.9s @22:07:26）；Python 3.13.5、PyInstaller 6.22.3；glfw3.dll / MSVCR90.dll 为已登记 WARNING，不影响构建结论 |

---

**打包状态**：`dist/ClashOverlay.exe` 最终件 88,468,375 B @22:07:26（BUILD OK 34.9s），含单屏放行、设置页修复、按钮 ID 修复，包码同步；后续重建与试跑口径以打包线为准。§1–§3 早期数字仍来自 `out/overlay/` 已落盘产物，不改已确认口径。
