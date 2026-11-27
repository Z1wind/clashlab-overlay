# -*- coding: utf-8 -*-
import glob, json, os, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
for p in sorted(glob.glob(os.path.join(BASE, "out", "annotate", "0*_annotated.json"))):
    d = json.load(open(p, encoding="utf-8"))
    note = d.get("note") or ""
    m = re.search(r"clashofclans-layouts\.com\s*#?(\d+)", note)
    quad = re.search(r"quad=\[\[([^\]]+)\],\[([^\]]+)\],\[([^\]]+)\],\[([^\]]+)\]\]", note)
    kinds = set(b.get("type") for b in d.get("buildings") or [])
    print(os.path.basename(p), "| id:", m.group(1) if m else None, "| quad?", bool(quad), "| types:", len(kinds))
    if quad:
        print("   quad:", [[float(x) for x in g.split(",")] for g in quad.groups()])
