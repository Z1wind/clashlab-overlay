# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "auto_candidates.py")
t = open(p, encoding="utf-8").read()
if "recall=False" not in t:
    t = t.replace("               gate_threshold=0.85):",
                  "               gate_threshold=0.85, recall=False):")
    old = '''    picked = []
    for it in items:
        sep = max(1.2, it["size"] * 0.6)  # 允许相邻建筑（间距 2 格）保留
        if all(abs(it["tile"][0] - p["tile"][0]) >= sep or
               abs(it["tile"][1] - p["tile"][1]) >= sep for p in picked):
            picked.append(it)'''
    new = '''    picked = []
    for it in items:
        sep = max(0.8, it["size"] * (0.35 if recall else 0.6))
        def _clash(p):
            if recall and p["size"] != it["size"]:
                return False  # 召回模式：不同尺度视为不同候选
            return (abs(it["tile"][0] - p["tile"][0]) < sep and
                    abs(it["tile"][1] - p["tile"][1]) < sep)
        if not any(_clash(p) for p in picked):
            picked.append(it)'''
    if old in t:
        t = t.replace(old, new, 1)
        t = t.replace('''    if gate_only:
        for it in items:''',
'''    if recall:
        max_n = max(max_n, 80)
    if gate_only:
        for it in items:''')
        t = t.replace('"gate_only": bool(gate_only),',
                      '"gate_only": bool(gate_only), "recall": bool(recall),')
        open(p, "w", encoding="utf-8", newline="\n").write(t)
        print("recall mode added")
    else:
        print("dedupe anchor miss")
p2 = os.path.join(BASE, "clashlab", "annotator.py")
t2 = open(p2, encoding="utf-8").read()
if "recall_mode" not in t2 and 'recall=bool' not in t2:
    t2 = t2.replace("gate_threshold=float(doc.get(\"gate_threshold\") or 0.85))",
                    "gate_threshold=float(doc.get(\"gate_threshold\") or 0.85),\n                                         recall=bool(doc.get(\"recall\")))")
    open(p2, "w", encoding="utf-8", newline="\n").write(t2)
    print("annotator recall param")
