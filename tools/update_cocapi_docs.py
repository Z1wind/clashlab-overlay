# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
def c(s): return BT + s + BT

# COCAPI 文档
doc = '''# 数据驱动：ClashKing 公开 API（TH / 部落战成员）

借鉴 [ClashKingBot](https://github.com/ClashKingInc/ClashKingBot) 的思路：**能拿数据的就别让用户手填**。
公开端点不需要 token（实测 2026-11-26）：

| 端点 | 能给什么 |
|---|---|
| @@@/v2/player/{tag}/war/attacks@@@ | 最近 50 条攻防记录，含 attackerTownhall / defenderTownhall |
| @@@/v2/clan/{clan}/wars@@@ | 最近/当前部落战，双方成员含 townhallLevel / mapPosition |

拿不到的（需要 Supercell 官方 API token）：英雄等级、兵种等级、装备等级、玩家完整档案。

## 用法

@@@powershell
python tools\\cocapi_cli.py --player '#QCRJPL2RJ'        # -> TH 16（取最近一场战争）
python tools\\cocapi_cli.py --clan '#2GYU8JRPV'          # 当前战争双方 20 人 TH
python tools\\cocapi_cli.py --auto-levels out\\annotate\\03_annotated.json --th 16
@@@

## 实测（2026-11-26）

- 玩家 @@@#QCRJPL2RJ@@@（z1wind）→ **TH 16**（最近战争 defend 记录 TH16；历史 TH11 记录被忽略）
- 部落 @@@#2GYU8JRPV@@@ 当前战争 20v20，双方成员 TH 14–19；
- @@@apply_th_levels@@@ 按 reviewed ruleset 的该 TH 最高等级回填布局建筑等级。

## 与「无脑化」的关系

1. 用户给玩家标签 → 自动知道 TH（以及部落战对手每个位置的 TH）
2. 敌方布局等级默认按 TH 回填 → 不用手工标
3. 识别只负责「建筑在哪、是什么类型」，等级由数据补
4. 若申请官方 API token：可再自动补英雄/兵种/装备等级（接口已预留，token 不进仓库）
'''.replace("@@@", BT)
open(os.path.join(BASE, "docs", "COCAPI.md"), "w", encoding="utf-8", newline="\n").write(doc)

# RECOG_RESULTS 追加合成训练结果
p = os.path.join(BASE, "docs", "RECOG_RESULTS.md")
t = open(p, encoding="utf-8").read()
add = '''
## 2026-11-26 16:30 合成素材「类型 + 等级」双头模型（GPU）

素材：ClashKingAssets 逐级立绘（513 张 / 48 种建筑），合成 14,880 张 96×96 样本（29 种类型 / 372 个类型-等级组合）。
训练：RTX 4060 Laptop 8GB，torch 2.14.1+cu126，300 epoch，batch 256，bf16，约 6 分钟。

| 指标 | 数值 |
|---|---|
| 类型准确率（合成验证集） | **0.9792** |
| 等级 MAE（平均差几级） | **1.135** |

产物：@@@models/synth_level.pt@@@（685,635 B）+ @@@models/synth_level_metrics.json@@@。

局限：这是**合成集**指标（立绘 + 随机背景），与真实截图有 domain gap；真实等级精度需要人工标几栋验证。
'''.replace("@@@", BT)
if "合成素材「类型 + 等级」" not in t:
    t = t.rstrip() + "\n" + add
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("docs updated")
