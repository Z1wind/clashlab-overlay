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
