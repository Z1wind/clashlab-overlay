# -*- coding: utf-8 -*-
import os, sys, json
from collections import Counter
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
for name in ("01","03","06"):
    d = json.load(open(os.path.join(BASE, "bases", "th16", name, "layout.json"), encoding="utf-8"))
    walls = d.get("walls") or []
    lens = Counter(len(w) if isinstance(w, (list, tuple)) else -1 for w in walls)
    print("==", name, "walls", len(walls), "item_len", dict(lens))
    print("  sample:", [walls[i] for i in range(0, min(6, len(walls)))])
    print("  last:", walls[-3:])
    # 与建筑 tile 的重合度
    bt = {(int(b["tile"][0]), int(b["tile"][1])) for b in d["buildings"] if b.get("tile")}
    wt = walls if all(isinstance(w, (list, tuple)) and len(w) == 2 for w in walls) else []
    overlap = len({(int(w[0]), int(w[1])) for w in wt} & bt) if wt else "n/a"
    print("  walls∩building_tiles =", overlap, "note:", (d.get("note") or "")[:80])
