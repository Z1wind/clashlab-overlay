# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
doc = '''# 批量阵型压测（穿云箭选线 + 英雄落点敏感性）

2026-11-26，工具：@tools/batch_arrow_test2.py@，报告：@out/arrow_batch/report.json@（不入库）。

## 样本（98 例）

| 来源 | 数量 | 说明 |
|---|---|---|
| 真实标注阵（6 阵 × 6 种变体） | 78 | 原图/镜像/旋转90/对角翻/平移±2 |
| 程序生成阵 | 20 | 26 栋防御随机撒点（含吹风机/防空火箭） |

> 真实战图：ClashKing 的 @/v2/bases/*@ 布局接口返回 **401**（要授权）；游戏内 UI 盲扫 9 个坐标未能打开部落战入口，所以本轮没有新增真实战图。

## 结果

| 指标 | 全部 98 | 真实 78 | 生成 20 |
|---|---|---|---|
| 落点稳定（±0.5 格内箭线命中的建筑集合不变） | 25（26%） | 21（27%） | 4（20%） |
| 出现最近目标翻转 | 13 | 11 | 2 |
| 最优箭线串到吹风机 | 78 | 58 | 20 |

最不稳定案例（±0.5 格内出现 19 种不同箭线）：
- @03-ann-shiftn2@（空投点附近有金矿/圣水收集器这种低血建筑，最近目标会跳）
- @05-ann-shift2@、@01-ann-shift2@、@06-ann-orig@（社区阵，落点选在储金罐附近）

## 结论

1. **英雄落点确实极度敏感**：98 例里只有 26% 的落点在 ±0.5 格内保持箭线命中不变——你担心的“中心偏移导致换目标”被数据证实。
2. **低血资源建筑是陷阱**：金矿/圣水收集器/储金罐常抢走“最近目标”，把箭线拉偏；规划时应把英雄落点放在**对空目标**（吹风机/防空）一侧，别贴着资源建筑。
3. 选线本身稳定：吹风机优先的自动选线在 78/98 例能串到吹风机，真实阵 58/78。
4. 用 @tools/arrow_placement_cli.py@ 对具体落点先跑敏感性；@stable=False@ 禁止实战。

## 想继续加真实战图

需要二选一：
- 游戏里进入**部落战侦察界面**（顶部显示对手名字/部落），我 ADB 截图 + OCR + API（已实现）；
- 或给 ClashKing UserToken/DeveloperToken，走 @/v2/bases/*@ 直接拉布局。
'''.replace("@@@", BT)
open(os.path.join(BASE, "docs", "ARROW_BATCH.md"), "w", encoding="utf-8", newline="\n").write(doc)

p = os.path.join(BASE, "README.md")
t = open(p, encoding="utf-8").read()
add = ("- **批量压测**：98 例（真实 6 阵 × 6 变体 + 20 生成阵）跑穿云箭选线/落点敏感性，仅 26% 落点稳定、13 例目标翻转（@docs/ARROW_BATCH.md@）。\n").replace("@", BT)
if "批量压测" not in t:
    anchor = "## 🗺 路线图"
    t = t.replace(anchor, add + "\n" + anchor, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("README updated")

p2 = os.path.join(BASE, "CHANGELOG.md")
t2 = open(p2, encoding="utf-8").read()
if "批量压测" not in t2:
    t2 = t2.replace("## v0.3.0 (unreleased)\n",
                    "## v0.3.0 (unreleased)\n- 批量阵型压测 98 例：落点稳定率 26%、13 例目标翻转（docs/ARROW_BATCH.md）。\n", 1)
    open(p2, "w", encoding="utf-8", newline="\n").write(t2)
    print("CHANGELOG updated")
