# -*- coding: utf-8 -*-
"""把 01_annotated.json（旧布局标注）转成 v2 导出格式，供训练链烟测。"""
import json, os, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ann = json.load(open(os.path.join(BASE, "out", "annotate", "01_annotated.json"), encoding="utf-8"))
m = re.search(r"quad=\[\[([^\]]+)\],\[([^\]]+)\],\[([^\]]+)\],\[([^\]]+)\]\]", ann.get("note") or "")
q = [[float(v) for v in g.split(",")] for g in m.groups()]
W, H = 1600, 735
sc = W / 2622.0
doc = {"version": 2, "image": "img/b01.jpg", "image_size": [W, H], "grid": 44,
       "corners": [[x * sc, y * sc] for x, y in q],
       "corners_norm": [[x * sc / W, y * sc / H] for x, y in q],
       "buildings": [{"type": b["type"], "name": b.get("name") or b["type"], "tile": b["tile"]} for b in ann["buildings"]]}
out = os.path.join(BASE, "out", "apk_qa", "smoke_export.json")
json.dump(doc, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", out, "buildings:", len(doc["buildings"]))
