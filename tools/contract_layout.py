# -*- coding: utf-8 -*-
"""从 corrected 生成契约用布局：瓦片 clamp 到 [0,43]，越界点压到边界；
不改 gold/证明文件，仅供 study/marks/prebattle 消费。"""
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = json.load(open(os.path.join(ROOT, "out/snap/corrected_home_village.json"), encoding="utf-8"))
out = {"name": "home_village_contract", "grid": 44, "source": "clamped_corrected",
       "note": "corrected 瓦片 clamp 到 0..43 供契约子命令消费；gold 与证明文件不变。",
       "buildings": []}
for b in src["buildings"]:
    t = [max(0, min(43, int(v))) for v in b["tile"]]
    nb = dict(b)
    nb["tile"] = t
    out["buildings"].append(nb)
dst = os.path.join(ROOT, "out/snap/contract_home_layout.json")
json.dump(out, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("buildings", len(out["buildings"]), "->", os.path.relpath(dst, ROOT))
