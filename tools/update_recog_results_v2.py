# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
def c(s): return BT + s + BT
p = os.path.join(BASE, "docs", "RECOG_RESULTS.md")
t = open(p, encoding="utf-8").read()
add = '''
## 2026-11-26 15:45 合并 APK 导出后再训（473 栋，含用户补标的零碎建筑）

用户用 Android APK 补标 03–06 阵（导出 JSON 合并后 6 阵共 **473 栋**，等级全部回填）：

| 配置 | 样本 | 类别 | within-5fold | LOBO | 产物 |
|---|---|---|---|---|---|
| 全类（32 类） | 473 | 32 | **0.8795** | **0.8199** | models/v2_all/recog_v2_all.pt |
| 仅防御（19 类） | 283 | 19 | **0.8799** | **0.8092** | models/v2_defense/recog_v2_def.pt |

分阵 LOBO（全类）：01 0.814 / 02 0.630 / 03 0.987 / 04 0.883 / 05 0.895 / **06 0.724**（比补标前的 0.278 大涨）。
对照：262 栋全类 within 0.718 / LOBO 0.581；154 栋旧模型 0.662 / 0.503。

结论：**06 阵补标是这轮最大收益**；全类模型现在 LOBO 0.820，已明显优于仅防御（0.809），
推荐作为默认识别模型；仅防御模型保留作对照。
'''.replace("@@@", BT)
if "15:45 合并 APK 导出后再训" not in t:
    t = t.rstrip() + "\n" + add
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("RECOG_RESULTS updated")
