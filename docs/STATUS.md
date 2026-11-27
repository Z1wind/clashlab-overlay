# 项目状态 / 待办（2026-11-26 收工）

> 明天接着做时的入口：本文件。上=已完成，下=待办（按优先级）。

## ✅ 已完成（2026-11-26）

### 识别 / 模型
- 合成素材「类型+等级」双头模型：14,880 样本、GPU（RTX 4060）300 epoch，合成集 type_acc **0.979** / level_mae **1.14**（`models/synth_level.pt`）
- 473 栋用户补标重训：全类 within **0.879** / LOBO **0.820**；仅防御 0.880/0.809
- 识别模型评估结论：分类器不再加投（瓶颈是检测），见 `docs/RECOG_DECISION.md`

### 数据驱动（ClashKing）
- 公开 API：玩家名→tag/TH、部落→战争成员 TH、按 warEndTime 取最新 TH（`clashlab/cocapi.py`）
- 实机 OCR+API 成功：真实部落战侦察屏 → SHADOW #PLVYQ0G2U **TH17**（`docs/LIVE_TEST.md`）
- 修复多行玩家名解析（SUVRO / Sumon 2 → #LR8GVY892 TH16）
- 可选 token 通道：`personal_bases()` / `server_bases()` + `tools/ck_bases_cli.py`（布局库接口需登录，401 已实测）
- GitHub 致谢 ClashKing + Hog Rider 申请英文模板（`docs/CLASHKING_APPLICATION.md`）

### 战术 / 兵棋
- 穿云箭：吹风机计入对空、特斯拉默认隐身（灰?/负收益）、自动选线（吹风机优先）
- 批量压测 **98 例**：落点稳定仅 **26%**、**13 例目标翻转**（`docs/ARROW_BATCH.md`）
- 英雄落点→最近建筑中心→箭线方向 + ±0.5 格敏感性 CLI（`tools/arrow_placement_cli.py`）
- 2D 渲染/评分/策略/放兵线沿用

### 工具 / 界面
- 本地网页标注器：`tools/annotate_web.py`（4 角标定 + 点建筑 + 导出 JSON，纯标准库）
- 敌方阵型流水线：`tools/enemy_pipeline.py`（评分+弱点+箭线+敏感性）
- 三语 UI：中文/繁體/English（标签栏右上角 中 繁 EN），`--lang` / `CLASHLAB_LANG`
- 英文文案润色 + 按钮 tooltip（自动采集/生成策略/触发研究）
- HUD 穿云箭图层（读 `config/giant_arrow_overlay.json`）
- 覆盖层修复：多开时选对 CoC 实例、面板高度 700、语言行重叠、imgui 多色回退、PANEL 绘制 NameError

## ⏳ 待办（优先级从高到低）

### P0（下次先做）
1. **PANEL 鼠标双通道冲突**：GLFW 原生事件 + `_feed_panel_mouse` 同时注入，导致点击标签页不切换（已定位，未修）。修法：只在窗口未聚焦/原生事件缺失时喂鼠标，或单一事件源；验收：自动点击四个标签页都能切换。
2. **研究页下移修复的视觉验证**：本地面板 +18px 已改，尚未截图确认不再压引擎说明。

### P1
3. 真实战图标注 → 跑 `enemy_pipeline.py`（标注器已就绪；用 `out/live/enemy_scout_live.png` 或新抓的战图）
4. HUD 穿云箭实机视觉验收（目标窗口已修，待游戏窗口在前台截图确认）
5. 面板异常窗口尺寸（出现过 997×561 HUD 尺寸）彻底排查（多实例/模式判定）

### P2
6. ClashKing token 拿到后：布局库批量拉取 → 批量真实阵压测
7. 剩余技术行/数据值保持英文原样（attack_close 等调试行建议折叠隐藏）
8. 检测器探索（合成+真实混合训练）—— 未启动，需单独立项

## 已知限制
- 检测器不可用（逐栋命中 0.06–0.16）；真实阵评分/箭线需人工标注位置
- ClashKing 布局接口需 token；公开端点无布局
- 夜世界（Builder Base）无数据模型
- 等级曲线为近似值；结论用于相对比较

## 💾 备份（GitHub Release）

- **backup-2026-11-26**（prerelease）：https://github.com/Z1wind/clashlab-overlay/releases/tag/backup-2026-11-26
- 资产：`ClashOverlay.exe`（121,346,737 B，md5 CEE1FBBB…）+ `clashlab_annotated_20261126.zip`（11,674,555 B，md5 1476B595…；含 6 阵标注 JSON、真实战图、批量压测报告）
- 源码：仓库 main 分支 + tag 的自动源码 zip
- 校验：下载 zip 实测 HTTP 200 / Content-Length 11,674,555 / md5 与本地一致


## 🔄 2026-11-27 更新（本轮处理 STATUS 待办）

### 已修 / 已验证
- **P0-1 鼠标双通道**：PANEL 默认不再注入自喂鼠标（配置项 `panel_mouse_feed: true` 可恢复）；exe 实测点击四个标签页 → 研究/阵型/采集/设置 均正确切换（OCR 底栏验证）。
- **P0-2 研究页重叠**：本地面板从 `content_top+56` 开始，刷新按钮/统计不再压引擎说明（截图 `out/live/research_final3.png`）。
- **P1-4 HUD 穿云箭**：HUD 实机截图可见箭线+编号；日志 `hud-arrow: plan from=[6.24,44] to=[23,0] hits_drawn=4`。
- **P1-5 异常窗口尺寸**：新增命名互斥 `ClashLabOverlaySingleton`；第二次启动实测日志 `another ClashLab overlay is already running; exit this instance`，窗口保持唯一 440×700。
- **P2-7 调试行**：锚点坐标调试行默认隐藏（`config/overlay.json` 的 `show_anchor_debug: true` 才显示）。

### 仍需人工 / 搁置
- **P1-3 真实战图标注**：自动模板匹配不可用（误匹配严重），需用 `tools/annotate_web.py` 人工点 3–5 分钟；标注后一条命令可跑 `tools/enemy_pipeline.py`。
- **P2-6 ClashKing token/布局库**：按要求本轮搁置。
- **P2-8 检测器**：未启动（需单独立项）。

## ❌ 2026-11-27：ClashKing / CoC API 通道关闭

ClashKing（Clash.Ninja）管理员明确回复：**模拟器使用本身是灰色地带、覆盖层可能违反 Supercell ToS**，且本项目不属于「通过官方 API 使用官方数据的常规工具」，因此**不提供 API/token 权限**。

- 决定：**不再申请 token、不接布局库**；`cocapi.py` 的 token 接口保留代码但标注为「不再推进」；
- 仅保留公开端点（玩家名→tag/TH、部落战成员）作为**可选**能力，是否使用由使用者自行评估；
- 项目主线转为**纯本地**：截图 → 标定 → 评分/推演/战术图，不依赖第三方授权。

## 📱 2026-11-27：手机标注 APK v2 + v0.3.0 Release

- APK：下载 https://github.com/Z1wind/clashlab-overlay/releases/download/v0.3.0/ClashLabAnnotator.apk
- 已内置 3 张真实战图；流程：点 4 个网格角 → 选类型点建筑 → 导出 JSON（保存到 Download）
- 实测：安装启动正常；导出 `apk2_export.json` schema=`clashlab-annotator-v2`，quad 4 点 + 1 栋 tile=[22,21]
- Release v0.3.0 资产：ClashOverlay.exe（121,348,119 B）、ClashLabAnnotator.apk（10,032,264 B）、标注数据 zip（11,674,555 B）

## 🔬 2026-11-27：检测器预研（C）已尝试并停止

- 合成检测集 1500/240（排除 firespitter/wall）→ CenterNet-mini 训练 12 epoch → 真实战图推理
- **结果：真实图 30 个框全部错位（UI/背景被当建筑），不达标** → 按预注册判据停止
- 详见 `docs/C_DETECT_SPIKE.md`；检测器可视化 `out/live/detect_cf_eval.png`
- 另外：firespitter 已在训练数据层排除（用户说明误标）；电脑标注器已在本机 8765 打开

## 🧪 2026-11-27：真实战图自动标注尝试（失败，见 AUTO_ANNOTATE_FAIL.md）

- 6 种自动标定方法 + quad_model + 滑窗分类器全部不可用；滑窗假阳性率 100%（无背景类）
- 结论：真实阵分析必须人工点 4 角 + 10–20 栋（约 2–3 分钟）；标注器已在 8765 运行

## 🚀 2026-11-27：本地路线第一批（P1 布局/规则层 + 一键入口）

- `clashlab/layout_grid.py`：44×44 逐格模型（墙折线/成对线段两种格式自动识别），提供隔间(flood fill)/孤立墙/大本是否被墙包/结构校验；wall 数据不完整时标 `wall_confidence=low`
- `clashlab/layout_rules.py`：8 条可解释规则（R1 大本墙体、R2 居中、R3 防空覆盖、R4 吹风机、R5 隔间、R6 墙体连贯、R7 仓库贴边、R8 核心防御多样），输出通过/跳过/证据/建议 + 分数等级；墙数据不完整时墙类规则自动 skip（不误判）
- `tools/auto_report.py`：一条命令入口 —— `--layout` 出报告 / `--dir` 批量 / `--image` 自动标定(带几何合理性校验，拒绝假阳性) + 找同名标注
- `tools/enemy_pipeline.py` 增加 `rules_eval` 输出
- 测试：全量 **322 tests OK**（新增 layout_grid 4 项 + layout_rules 3 项）
