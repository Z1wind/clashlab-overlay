# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
def c(s): return BT + s + BT
lines = [
 "",
 "## 2026-11-27 门控召回模式（方案 1）",
 "",
 "- auto_candidates 新增 recall 模式：多尺度不合并 + 去重距离缩小 -> 候选数 17 -> 71（thr 0.70）/ 80（thr 0.55）",
 "- 标注器页面加「召回优先」复选框 + 阈值滑块（0.50–0.98）",
 "- E2E 实测：recall=False thr0.85 -> items=17；recall=True thr0.70 -> items=71；thr0.55 -> items=80（上限 80）",
 "- 覆盖评估：71 个候选基本铺满基地（截图 out/live/gate_recall070.png），但包含少量墙/空地误报；实际 70+ 栋，覆盖率显著提升",
 "- 350 测试 OK",
]
p = os.path.join(BASE, "docs", "STATUS.md")
t = open(p, encoding="utf-8").read()
if "门控召回模式" not in t:
    open(p, "w", encoding="utf-8", newline="\n").write(t.rstrip() + "\n" + "\n".join(lines) + "\n")
    print("STATUS updated")
