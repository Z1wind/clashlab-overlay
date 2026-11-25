# -*- coding: utf-8 -*-
"""配准独立校验：对比我方 gold calib 与引擎 quad 在 8 个锚点上的 tile 差异。
读取 out/snap/engine_quad.json（引擎 v2 grid_check.png 所用 quad），
|Δ|>1 格判配准不合格，记录偏差方向。本脚本只做坐标对比，不采信引擎结论。
"""
import os, sys, json, math
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from clashlab.geo import Calib

g = json.load(open(os.path.join(ROOT, "out/snap/gold/home_village_gold.json"), encoding="utf-8"))
mine = Calib.from_dict(g["calib"])
eq = json.load(open(os.path.join(ROOT, "out/snap/engine_quad.json"), encoding="utf-8"))["quad"]
eng = Calib.from_quad(eq, 44)

ANCHORS = {
    "TH_若可见": (898, 428),
    "西北角墙段": (300, 250),
    "东北角墙段": (985, 255),
    "西南角墙段": (220, 470),
    "东南角墙段": (905, 430),
    "边上箭塔_h11": (272, 318),
    "边上箭塔_h22": (832, 222),
    "迫击炮_h28": (732, 428),
}
print("anchor,px,mine_tile,engine_tile,dTx,dTy,dist_tile,verdict")
bad = 0
for name, (px, py) in ANCHORS.items():
    mx, my = mine.px_to_tile(px, py)
    ex, ey = eng.px_to_tile(px, py)
    d = math.hypot(ex - mx, ey - my)
    if d > 1.0:
        bad += 1
    verdict = "FAIL" if d > 1.0 else "OK"
    print(f"{name},({px},{py}),({mx:.2f},{my:.2f}),({ex:.2f},{ey:.2f}),{ex-mx:+.2f},{ey-my:+.2f},{d:.2f},{verdict}")
print(f"FAIL={bad}/8  {'配准不合格' if bad else '配准合格（全部≤1格）'}")
