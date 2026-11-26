# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
def c(s): return BT + s + BT

p = os.path.join(BASE, "docs", "RECOG_RESULTS.md")
t = open(p, encoding="utf-8").read()
add = '''
## 2026-11-26 重训（用户补标后，6 阵 262 栋）

数据：@@@out/annotate/01..06_annotated.json@@@（262 栋，32 类；仅防御类 190 栋 / 19 类）。
命令：

@@@powershell
python tools\\train_save_model.py --layouts "out\\annotate\\*_annotated.json" --epochs 40 \\
  --models-dir models\\all6_all --checkpoint recog_all6.pt
python tools\\train_save_model.py --layouts "out\\annotate\\*_annotated.json" --only-defense --epochs 40 \\
  --models-dir models\\all6_defense --checkpoint recog_all6_def.pt
@@@

| 配置 | 样本 | 类别 | within-5fold | LOBO | 产物 |
|---|---|---|---|---|---|
| 6 阵 · 全部类型 | 262 | 32 | **0.718** | **0.581** | models/all6_all/recog_all6.pt |
| **6 阵 · 仅防御类** | 190 | 19 | **0.853** | **0.767** | models/all6_defense/recog_all6_def.pt |

分阵 LOBO（仅防御模型）：01 0.830 / 02 0.625 / 03 0.929 / 04 0.958 / 05 0.917 / **06 0.278**。
06 只有 18 栋，跨阵最不稳定；02 的 0.625 主要是经济类混标错误被去掉后仍缺样本。

对照（同日之前）：旧 154 样本全类模型 within 0.662 / LOBO 0.503；两阵 168 样本全类 within 0.571 / LOBO 0.355。
结论：**补标 + 只保留防御类**是这轮提升的主因；识别链路现在有可用的跨阵泛化（LOBO 0.767）。

局限：颜色/等级仍未进标签；06 阵样本太少；经济类不参与训练（只做布局用）。
'''.replace("@@@", BT)
if "2026-11-26 重训" not in t:
    t = t.rstrip() + "\n" + add
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("RECOG_RESULTS updated")

# README 最近更新数字
p2 = os.path.join(BASE, "README.md")
t2 = open(p2, encoding="utf-8").read()
old = "（默认 40 epoch：within 0.662 / LOBO 0.503；60 epoch 可到 0.734 / 0.641）"
new = "（2026-11-26 补标后 6 阵 262 栋重训：全类 within 0.718 / LOBO 0.581；**仅防御类 within 0.853 / LOBO 0.767**）"
if old in t2:
    t2 = t2.replace(old, new)
    open(p2, "w", encoding="utf-8", newline="\n").write(t2)
    print("README zh updated")
p3 = os.path.join(BASE, "README.en.md")
t3 = open(p3, encoding="utf-8").read()
old3 = "(40-epoch default: within 0.662 / LOBO 0.503; 0.734 / 0.641 at 60 epochs)"
new3 = "(retrained 2026-11-26 on 6 bases/262 buildings: all classes within 0.718 / LOBO 0.581; **defense-only within 0.853 / LOBO 0.767**)"
if old3 in t3:
    t3 = t3.replace(old3, new3)
    open(p3, "w", encoding="utf-8", newline="\n").write(t3)
    print("README en updated")
