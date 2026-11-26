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
