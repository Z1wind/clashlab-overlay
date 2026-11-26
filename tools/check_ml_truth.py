# -*- coding: utf-8 -*-
import json, os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
m = json.load(open(os.path.join(BASE, "models", "metrics.json"), encoding="utf-8"))
print("generated:", m.get("generated_at"), "| epochs:", (m.get("train") or {}).get("epochs"))
print("within:", (m.get("within_5fold") or {}).get("accuracy"), "| n:", (m.get("within_5fold") or {}).get("n"))
print("lobo:", (m.get("lobo") or {}).get("accuracy"), "| n:", (m.get("lobo") or {}).get("n"))
# ML doc table lines
p = os.path.join(BASE, "docs", "ML_FEASIBILITY.md")
for i, line in enumerate(open(p, encoding="utf-8").read().splitlines(), 1):
    if any(k in line for k in ("0.6", "0.5", "0.7", "epoch", "within", "LOBO", "checkpoint")):
        print(i, ":", line[:140])
