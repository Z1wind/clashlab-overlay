# -*- coding: utf-8 -*-
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab import auto_candidates as ac
IMG = os.path.join(BASE, "out", "live", "hires", "coc_193842_6.png")
quad = json.load(open(os.path.join(BASE, "out", "live", "hires_hough_quad.json"), encoding="utf-8"))["quad"]
print("%-8s %-8s %-10s" % ("thr", "items", "gated"))
for thr in (0.30, 0.40, 0.50, 0.60, 0.70):
    r = ac.candidates(IMG, quad, max_n=90, gate_only=True, gate_threshold=thr, recall=True)
    print("%-8.2f %-8d %-10s" % (thr, len(r.get("items") or []), r.get("gated_counts")))
