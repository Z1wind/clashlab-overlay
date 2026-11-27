# -*- coding: utf-8 -*-
import glob, json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
for d in sorted(glob.glob(os.path.join(BASE, "out", "enemy_report", "0*_annotated"))):
    f = os.path.join(d, "report.json")
    r = json.load(open(f, encoding="utf-8"))
    re_ = r.get("rules_eval") or {}
    print(os.path.basename(d), "rules score:", re_.get("score"), re_.get("grade"),
          "| failed:", [x["id"] for x in re_.get("failed") or []],
          "| comps:", re_.get("wall_compartments"), "iso:", re_.get("wall_isolated_ratio"))
