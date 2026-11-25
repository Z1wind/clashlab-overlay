# -*- coding: utf-8 -*-
import os, json
from collections import Counter
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
for b in ("03", "05"):
    d = json.load(open(os.path.join(BASE, "bases", "th16", b, "layout.json"), encoding="utf-8"))
    print("==", b, "keys", list(d.keys()))
    print("  grid", d.get("grid"), "buildings", len(d.get("buildings", [])), "walls", len(d.get("walls") or []))
    print("  building[0]", json.dumps(d["buildings"][0], ensure_ascii=False))
    print("  wall[0]", json.dumps((d.get("walls") or [None])[0], ensure_ascii=False))
    print("  types", dict(Counter(x["type"] for x in d["buildings"])))
