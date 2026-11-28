# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
with open(os.path.join(BASE, "docs", "WORKLOG.md"), "a", encoding="utf-8", newline="\n") as f:
    f.write("\n".join([
        "",
        "## 用户思路（先1后2）结果（2026-11-28 19:10）",
        "- 数据更新：重标 b01/b02 后全 8 张可用（b01 90 栋 / b02 92 栋，纹理能量接近正常）",
        "- 分类器 8 张 CV：top1 95.4% / top3 98.2%",
        "- 方案1 embedding(ArcFace)+背景类 最近邻：P44.7 R71.4 F1 .540 type 96.3%",
        "- 方案2 混合（CNN 门控 + embedding 最近邻/背景校验）：P62.3 R71.0 F1 .658 type 91.8% ← 当前最佳",
        "- 对比软分类流水线：P70.4 R53.2 F1 .597 type 83.1%",
        "- 结论：用户「特征比对」思路在「门控 + 学习特征最近邻」组合下有效：召回 53→71（+18pt）、类型 83→92（+9pt），精度让 8pt",
        "",
    ]))
print("worklog updated")
