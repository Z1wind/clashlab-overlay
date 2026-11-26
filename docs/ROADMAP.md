# 路线图与今日方向（2026-11-26，Lead 自主推进）

用户给了三个方向、没时间逐个确认，我按下面并行推进：

## 一、赛前「兵棋推演」新功能

- 目标：把「军队构成 + 投放点」变成可量化的战局推演（摧毁率分布、最佳投放点），作为赛前简报的一部分。
- 参考：[NathanNT/clash-battle-engine](https://github.com/NathanNT/clash-battle-engine)（MIT，C++20，确定性 battle simulator，含 format/architecture 文档），只借鉴设计与数据格式，不复制代码。
- 交付：`clashlab/wargame.py`（确定性 tick + Monte Carlo）、`tools/wargame_cli.py`、`tests/test_wargame.py`、`docs/WARGAME.md`；后续接 `prebattle` 输出与 PANEL 推演行。

## 二、实机端到端证明（绘制/界面可用）

- 目标：用真实运行矩阵证明 HUD/PANEL 的绘制与交互，不只是单测。
- 交付：`tools/qa_e2e.py`（可复跑矩阵）+ `docs/QA_E2E.md`（每项：命令 / 截图 / 日志 / PASS-FAIL）+ `out/qa_e2e/` 截图。
- 覆盖：HUD/PANEL × 有/无布局、研究页/阵型页、改窗口尺寸触发重标定、EXE 自检。

## 三、机器学习可行性证明

- 目标：训练→评估→保存模型→推理接口→可复现文档，一条闭环。
- 交付：`tools/train_save_model.py`、`clashlab/recog_model.py`、`tests/test_recog_model.py`、`docs/ML_FEASIBILITY.md`、`models/`（checkpoint + metrics）。
- 已有数据结果（标注驱动）：within-5fold **0.734**、LOBO **0.641**（对照原始 layout 0.435）。

## 领导裁定（记录在案）

- 「追踪者的兵棋项目」未能在其公开仓库里定位（`akermu666` 公开仓库 0 个；`drkostas` 89 个仓库中无 wargame/simulator），因此按兵棋推演的通用能力自建，并在文档中向 `NathanNT/clash-battle-engine` 致敬。
- 不自动操作游戏（不点「重新载入游戏」等），实机验证遇到断线弹窗时记录为「未实测」而不是伪造 PASS。

## 第四阶段（2026-11-26 起，用户新需求）

1. **全大本营支持（TH1–TH19）**：`clashlab/th_data.py` 逐档数据 + 可信度标注；`assets.stats(name, th)` 委托该表；识别模型目前仅覆盖 TH16 的 19 类，其他档依赖标注数据。
2. **布阵 → 兵种搭配推荐 + 联网打法 + 视频入口**：`clashlab/strategy.py` 由弱点驱动推荐（空军/地面/英雄切入），附投放步骤与 YouTube 搜索链接（不抓取第三方内容）；数据 `knowledge/strategies.json`。
3. **后续（未开始）**：战术卡与英雄装备使用攻略（`knowledge/hero_equipment.json` 骨架先行，UI 接入待定）。

## 已知限制（持续维护）

- 兵棋推演数值为近似表，只做相对排序，未与真实战报校准；
- 实机 QA 中物理鼠标点击未实测（系统注入被冻结），页签切换用进程内事件注入验证；
- TH17–19 的建筑数值部分来自公开资料且 confidence 较低，导入/评分前请看 `docs/TH_SUPPORT.md`。
