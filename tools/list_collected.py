# -*- coding: utf-8 -*-
import glob, json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
OUT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\live\scouts"
rows = []
for f in sorted(glob.glob(os.path.join(OUT, "*.json"))):
    if "_" in os.path.basename(f) and os.path.basename(f).startswith("_"):
        continue
    try:
        d = json.load(open(f, encoding="utf-8"))
    except Exception:
        continue
    p = (d.get("api") or {}).get("player") or {}
    rows.append((os.path.basename(f), d.get("ocr", {}).get("name"), d.get("ocr", {}).get("clan"),
                 p.get("tag"), p.get("th")))
print("count:", len(rows))
for r in rows:
    print(r)
