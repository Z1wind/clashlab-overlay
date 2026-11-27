# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "auto_candidates.py")
t = open(p, encoding="utf-8").read()
if "gate_threshold=0.85" not in t:
    t = t.replace("def candidates(image_path, quad, max_n=30, min_conf=0.97, min_var=60.0, gate_only=False):",
                  "def candidates(image_path, quad, max_n=30, min_conf=0.97, min_var=60.0, gate_only=False,\n               gate_threshold=0.85):")
    t = t.replace("    gate_thr = 0.85\n", "    gate_thr = float(gate_threshold)\n")
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("threshold param added")
p2 = os.path.join(BASE, "clashlab", "annotator.py")
t2 = open(p2, encoding="utf-8").read()
if "gate_threshold" not in t2:
    t2 = t2.replace("gate_only=bool(doc.get(\"gate_only\")))",
                    "gate_only=bool(doc.get(\"gate_only\")),\n                                         gate_threshold=float(doc.get(\"gate_threshold\") or 0.85))")
    open(p2, "w", encoding="utf-8", newline="\n").write(t2)
    print("annotator threshold param")
