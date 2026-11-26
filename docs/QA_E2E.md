# 实机端到端 UI/绘制验证（QA_E2E）

- 日期：2026-11-26 10:16–10:18（Asia/Shanghai）
- 主机：Windows，Python 3.13（`D:\Python313\python.exe`），LDPlayer 9 + adb 就绪
- 屏幕：主屏 1920×1080 + 副屏 1920×1080（虚拟桌面 3840×1080）
- 目标窗口：产品 `find_render_target()` 选中 `LDPlayerMainFrame 0x209f4`（标题「雷电模拟器」，客户区 997×561 @ (32,401)）；运行中该实例显示 CoC「还在吗？…已断开连接」弹窗，不影响覆盖层绘制验证
- 另有一个雷电实例 `0x1c0db2` 在副屏 x=1955，产品按「最后一个可见主窗」规则未选它；复跑时窗口 Z 序变化可能改变被选实例
- **结论：7/7 PASS**；无 FAIL。物理鼠标点击页签未实测（本机 OS 级鼠标注入被冻结，见「限制」）

## 复跑

```powershell
cd "C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
D:\Python313\python.exe tools\qa_e2e.py
```

一条命令跑完全部 7 个用例（约 70–90 秒），退出码 0=全 PASS / 1=有 FAIL；截图写 `out/qa_e2e/`，逐例 stdout 写 `out/qa_e2e/logs/`，机读汇总写 `out/qa_e2e/summary.json`。脚本内 `finally` 恢复 `layouts/layout_current.json` 原状（本次原文件不存在 → 跑完删除）并还原窗口尺寸。

## 覆盖矩阵

| # | 项 | 命令 | 截图（文件 / 字节） | 日志关键行 | 结论 |
|---|---|---|---|---|---|
| 1 | HUD，无 `layouts/layout_current.json` | `python run_overlay.py --show --mode HUD --always-on-top --allow-primary --run-seconds 8` | `hud_nolayout.png` 736,634；`hud_nolayout_desktop.png` 3,310,665 | `overlay loop start; start_mode=HUD; always_on_top=True`；`overlay SHOW … reason=always-on-top`；`mode=HUD rect=(32,401,997x561)`；`fps summary frames=478 fps_mean=59.96 p99=17.729ms` | PASS |
| 2 | HUD，有 layout_current | 同上（脚本先写临时布局） | `hud_layout.png` 735,889 | 同上；`fps summary frames=478 fps_mean=59.94 p99=17.702ms`；与 #1 截图差异 3.87%（游戏动画/取帧时刻差；HUD 绘制不消费 layout_current） | PASS |
| 3 | PANEL，无布局 | `python run_overlay.py --show --mode PANEL --always-on-top --allow-primary --run-seconds 8` | `panel_nolayout.png` 61,442 | `panel_position=right -> right`；`mode switch HUD->PANEL … after=0x000c0098`；`exstyle assert cycle=1 OK mode=PANEL`；`PANEL draw container first frame: panel_w=440 W=440 H=561`；`fps_mean=60.98` | PASS |
| 4 | PANEL，有布局 | 同上（脚本先写临时布局） | `panel_layout.png` 73,457 | 同上；状态行由「阵型 已加载 · 候选 0」变为「阵型 已加载 · 候选 0 · 评分 70.9 B」，并多出弱点行与「推演：预估摧毁 20% · 最佳落点 (10,27)」；与 #3 差异 12.13% | PASS |
| 5 | PANEL 研究页 → 阵型页切换 | `python tools/qa_e2e.py --only panel_page`（内部 `python -c <QA_PAGE_HARNESS>` 启动 `runtime.run`，在进程内注入 ImGui 页签点击） | `panel_page_research.png` 73,473；`panel_page_layout.png` 71,439（内容差异 32.5%） | `QA harness: armed (hovering tab, research visible)`；`QA harness: inject tab click -> layout at (167.5,25.0)`；`QA harness: state.page=layout (wanted layout)`；`COLOR selfcheck TAB_SEL … amber #E8A33D`；`fps_mean=47.18` | PASS（注入点击）；物理鼠标点击**未实测** |
| 6 | HUD 运行中缩小窗口再还原 | `python run_overlay.py --show --mode HUD --always-on-top --allow-primary --run-seconds 12` + `win32gui.SetWindowPos`（−140×−90，1.5s 后还原） | `hud_resize.png` 736,276；`hud_resize_shrunk.png` 550,149；`hud_resize_restored.png` 741,698 | `viewport 997x561 -> 837x471; calib rebuilt (normalized scale, marks kept)`；`viewport 变化 >10%: 尝试一次自动重标定（失败归一化缩放兜底）`；`recalib: view_quads table adopted (no grab)`；还原后 `viewport 837x471 -> 997x561` + 同样的 recalib 两行；`fps_mean=61.27` | PASS |
| 7 | 打包 exe 自检 | `dist\ClashOverlay.exe --seconds 6 --no-show` | `exe_selfcheck_desktop.png` 3,302,109（自检不建窗口） | `self-check mode (invisible) start`；`marks keys=[…] marks=5 pins=6 circles=1 steps=6`；`calib tile (32, 22) -> px (743.3,470.8)`；`self-check done in 6.0s (no window shown)`；exit=0，未见 ClashOverlay 可见窗口 | PASS |

## 关键证据

- #1 的 HUD 绘制：`hud_nolayout.png` 中可见顶部 `HUD live=dry`、`鹰炮 350`、`防空`、`散射炮` 等标注与底部 `Insert 打开面板` 提示；`hud_nolayout_desktop.png` 为 3840×1080 全桌面，确认覆盖层确实贴在雷电客户区而非离线合成。
- #4/#5 的差异不是噪声：`panel_layout.png` 状态行多了「评分 70.9 B」，研究页多了弱点行与推演行（`score_card` + `sim_panel` 消费 `state.layout`）；`panel_page_layout.png` 顶部「阵型」页签呈琥珀选中态，内容为阵型画布/候选筛选/冻结 layout。
- #6 两次 `viewport … calib rebuilt` 与两次 `recalib: view_quads table adopted` 成对出现，证明「改尺寸→自动重标定→还原→再标定」整条链路生效；还原后主窗矩形回到 `(31,367,1067,962)`。
- 逐例完整 stdout：`out/qa_e2e/logs/<case>.stdout.log`；机读汇总：`out/qa_e2e/summary.json`。

## 失败项

无（0 FAIL）。若有 FAIL，`tools/qa_e2e.py` 会在汇总中打印 FAIL + 该例日志尾部并以退出码 1 结束；本次无需记录失败现象/尾段。

## 限制与未实测

1. **OS 级鼠标注入被冻结**：`SetCursorPos` 返回失败、`SendInput` 返回 1 但光标坐标不变（实测冻结在 (3187,946)，且 `ClipCursor` 为整虚拟桌面）。因此 #5 不能做真实物理点击，改为在 overlay 进程内把 `mouse_pos/mouse_button` 事件喂给 ImGui；点击仍走 `pages._tab_row` 的真实 `imgui.button` → `ctx.set_page("layout")` 路径，并由 `state.page=layout` 与两页截图差异（32.5%）佐证。**「用真实鼠标点页签」这一物理链路未实测。**
2. 目标实例当前停在 CoC 断线重连弹窗（`还在吗？…重新载入游戏`）；HUD 标注绘制与窗口跟随已验证，但「战斗中的干净帧」未取。
3. `dist\ClashOverlay.exe` 为 `console=False`，无 stdout；#7 的证据是 `out/overlay/overlay.log` 的增量、exit=0 和桌面截图。按约束未重新打包 dist。
4. HUD 不消费 `layouts/layout_current.json`（`state.layout` 仅 PANEL 研究/阵型页使用）；#1/#2 的 3.87% 差异来自游戏动画与取帧时刻，不是布局导致的绘制差异。
5. 本机有两个雷电实例；产品选中规则是「最后一个可见 `LDPlayerMainFrame`」。复跑前若调整过窗口 Z 序/实例，`find_render_target` 可能改选副屏实例，届时截图的裁切坐标会随日志里的 `mode=… rect=…` 自动变化。

## 恢复与清理

- `layouts/layout_current.json`：测试前不存在；脚本用完即删（`summary.json` 中 `layout_original_present=false, layout_restored=true`）。
- 窗口尺寸：`SetWindowPos` 前保存 `GetWindowRect`，`finally` 还原；实测 `main_rect_restored == main_rect_orig`。
- 未改产品代码；仅新增 `tools/qa_e2e.py`、本文件与 `out/qa_e2e/` 产物。
