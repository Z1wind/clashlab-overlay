# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
with open(os.path.join(BASE, "docs", "WORKLOG.md"), "a", encoding="utf-8", newline="\n") as f:
    f.write("\n".join([
        "",
        "## 用户思路验证：关键贴图直接比对（2026-11-28 18:20）",
        "- 方案：拿已标建筑 4x4 窗口裁片当模板（每类最多 6 个），全图逐格 NCC 匹配 + 阈值扫描 + 距离去重",
        "- 全类型结果：prec 0.290 / recall 0.525 / f1 0.364 / type_acc 0.707（差于 CNN 流水线 P0.715/R0.456/F1 0.545）",
        "- 仅外形独特 13 类：prec 0.328 / recall 0.255 / f1 0.233（TH/EA/法术塔等命中时类型 100%，但误报极多）",
        "- 结论：原始像素 NCC 对视角/缩放/相邻建筑/等级变化不鲁棒，直接贴图比对打不过 CNN",
        "- 可行升级：用度量学习（embedding + 最近邻）代替原始 NCC，让「同类型不同基」聚在一起，再做比对",
        "- 产物：out/template_match_report.json、out/template_distinctive_report.json、tools/template_match_eval.py、tools/template_distinctive_eval.py",
        "",
    ]))
print("worklog updated")
