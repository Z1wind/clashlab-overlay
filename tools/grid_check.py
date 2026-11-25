# -*- coding: utf-8 -*-
"""独立配准校验（引擎 v2 交付 grid_check.png 后用）。
方法：选 5-8 个位置明确的建筑（大本营/四角墙段/边上箭塔），
用我方 gold calib 把像素中心反算 tile，再与引擎 grid_check.png 上该像素的格号目视比对；
偏差 >1 格判配准不合格，记录偏差方向。本脚本只输出我方坐标，不读引擎结论。
"""
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from clashlab.geo import Calib

g = json.load(open(os.path.join(ROOT, "out/snap/gold/home_village_gold.json"), encoding="utf-8"))
calib = Calib.from_dict(g["calib"])

# 位置明确的校验锚点（人工指定 px，不依赖候选）
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
for name, (px, py) in ANCHORS.items():
    tx, ty = calib.px_to_tile(px, py)
    print(f"{name}: px=({px},{py}) -> tile=({tx:.2f},{ty:.2f})")
print("用法：在 grid_check.png 同像素处读引擎格号，与上列对比，|Δ|>1 格判不合格。")
