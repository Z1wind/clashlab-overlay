# -*- coding: utf-8 -*-
"""人工 zoom 核对后修正 gold：h26 改标 unknown；新增 4 座 air-defense（h46-h49）。
只读校验脚本外的 gold 写入仅此一次，备份在 home_village_gold.v2pre_ad.bak.json。"""
import os, sys, json, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from clashlab.geo import Calib

gp = os.path.join(ROOT, "out/snap/gold/home_village_gold.json")
shutil.copyfile(gp, os.path.join(ROOT, "out/snap/gold/home_village_gold.v2pre_ad.bak.json"))
g = json.load(open(gp, encoding="utf-8"))
cal = Calib.from_dict(g["calib"])

# 1) h26 旧标 air-defense 误判：放大(612,392) 实为蓝色圆形工坊/攻城机器平台
for b in g["buildings"]:
    if b["id"] == "h26":
        b["type"] = "unknown"
        b["note"] = "旧标 air-defense 误判；zoom(612,392) 实为蓝色圆形工坊/攻城机器平台，非防空塔"
        b["verified_by"] = "human_zoom"

# 2) 4 座防空塔（人工 6x zoom 逐座核对：黄黑条纹塔身+粉紫发光芯）
NEW = [
    ("h46", [318, 205], "p1 zoom(330,215) 确认防空塔，黄黑条纹+粉紫芯"),
    ("h47", [1048, 388], "p2 zoom(1050,385) 确认防空塔，黄黑条纹+粉紫芯，邻暗黑重油钻井"),
    ("h48", [358, 495], "p3 zoom(360,490) 确认防空塔，黄黑条纹+粉紫芯"),
    ("h49", [690, 655], "p4 zoom(692,650) 确认防空塔，黄黑条纹+粉紫芯"),
]
for gid, fp, note in NEW:
    tx, ty = cal.px_to_tile(*fp)
    g["buildings"].append({
        "id": gid,
        "type": "air-defense",
        "tile": [int(round(tx)), int(round(ty))],
        "size_tiles": 3,
        "foot_px": fp,
        "foot_tile_raw": [round(tx, 3), round(ty, 3)],
        "note": note,
        "verified_by": "human_zoom",
    })

json.dump(g, open(gp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("gold total", len(g["buildings"]))
print("air-defense entries:", [b["id"] for b in g["buildings"] if b["type"] == "air-defense"])
