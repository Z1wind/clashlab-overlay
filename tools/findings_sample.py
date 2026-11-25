# -*- coding: utf-8 -*-
import os, sys, json
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab import defense_findings as df

rows = []
for name in ("01","02","03","04","05","06"):
    p = os.path.join(BASE, "bases", "th16", name, "layout.json")
    lay = json.load(open(p, encoding="utf-8"))
    fs = df.findings(lay)
    line = df.summary_line(fs)
    rows.append({"base": name, "summary": line, "findings": fs})
    print(name, "|", line, flush=True)
json.dump(rows, open(os.path.join(BASE, "out", "overlay", "_p3b", "tactical_findings_sample.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("saved")
