# 战术知识：隐形特斯拉 / 穿云箭目标

> 目的：把「攻略站 + 游戏机制 + 本仓数据」里学到的结论沉淀成可执行规则，避免凭感觉写代码。

## 1. 隐形特斯拉（Hidden Tesla）

- **不现形**：侦察/进攻开始前看不到；踩到或被攻击后才现身。所以布局图上的特斯拉格位只能是**推测**，不能当已确认目标。
- **DPS 低**：本仓 TH16 数据表：特斯拉 hp 1000 / dps **130**；对比防空火箭 dps 330、地狱塔 250、X 连弩 200、散射炮 290。清它收益低。
- **结论**：穿云箭/法术**不为特斯拉调整路线**；图上标灰 + 问号 + 橙色提醒，统计里单列「特斯拉隐身×n」，评分给负分（-0.5，按运气而非计划）。

## 2. 穿云箭（Giant Arrow）目标优先级

| 优先级 | 目标 | 理由 |
|---|---|---|
| 1 | **吹风机（air-sweeper）** | 自身 DPS 0，但吹风会打乱整片空军路线/时间轴；串掉一座通常比多串一座防空更值 |
| 2 | **防空火箭（air-defense）** | 对空 dps 330，是空军最大威胁 |
| 3 | 其它防御（散射炮/地狱塔/X 弩…） | 顺路串到算收益 |
| — | **特斯拉** | 默认不现形 + dps 130，按未知风险处理，不计收益 |

自动选线实现：`tools/giant_arrow_cli.py`（`optimize_giant_arrow`）——候选线=每座对空目标过点 4 方向 + 两座对空目标连线，裁到 44×44 地图内，按「吹风机数 → 评分 → 命中数」排序。

实测（base03）：最优线 `[6.24,44] → [23,0]`，命中吹风机×1 + 防空×1 + 散射炮/鹰炮；评分 7.0。

## 3. 数据来源

- Supercell 游戏内机制（特斯拉不现形、穿云箭直线伤害、吹风机只推不伤）
- coc.guide 数据库：Hidden Tesla（https://coc.guide/defense/hidden-tesla/）、Giant Arrow（https://coc.guide/equipment/giant-arrow/）
- 本仓 `clashlab/assets.py` + `knowledge/th_ruleset.json`（TH16 数值）

## 4. 代码落点

- `clashlab/overlay/giant_arrow_diagram.py`：AIR_TARGETS、HIDDEN_TYPES、summarize_hits、tesla_warning、score_hits、optimize_giant_arrow
- `knowledge/tactics.json`：机器可读的战术条目（含来源）
- 测试：`tests/test_giant_arrow_air.py`、`tests/test_giant_arrow_optimizer.py`、`tests/test_tesla_tactics.py`
