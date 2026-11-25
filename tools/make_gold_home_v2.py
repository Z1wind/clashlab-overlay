# -*- coding: utf-8 -*-
"""home gold v2：人工在干净象限图上读 px 中心，旧 H(与引擎标签空间一致) 换算 px_to_tile。
类型 best-effort；看不清的 type=null 并进 ambiguous。城墙段标为 wall。
"""
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from clashlab.geo import Calib
import numpy as np

human = json.load(open(os.path.join(ROOT, "out/snap/annot/human_H.json"), encoding="utf-8"))
calib = Calib(np.array(human["H"], dtype=np.float64), n=44, quad=np.array(human["quad"], dtype=np.float32))

# (id, type, px, note, ambiguous?)
ROWS = [
    # 墙外/左侧非库类
    ("h01", "builder-hut", (178, 158), "左侧木屋工匠棚，素材库无此类", True),
    ("h02", "army-camp", (232, 118), "红顶帐篷营地区，素材库无此类", True),
    # Q1
    ("h03", "collector", (332, 200), "紫滴圣水采集器", False),
    ("h04", "collector", (428, 158), "金币采集器", False),
    ("h05", "storage", (432, 272), "紫球95圣水瓶", False),
    ("h06", "collector", (158, 362), "金币采集器", False),
    ("h07", "collector", (158, 468), "紫滴圣水采集器", False),
    ("h08", "storage", (652, 238), "金堆储罐", False),
    ("h09", None, (588, 108), "红黑高塔，类型不定", True),
    ("h10", "storage", (508, 198), "金堆储罐（原误标 cannon，放大为金堆）", False),
    ("h11", "archer-tower", (272, 318), "白塔，箭塔", True),
    ("h12", "wizard-tower", (548, 328), "紫金镶边法师塔，疑似", True),
    # Q2
    ("h13", "collector", (768, 150), "紫滴圣水采集器", False),
    ("h14", "collector", (908, 168), "黑油采集器", False),
    ("h15", "storage", (918, 262), "金堆储罐", False),
    ("h16", "storage", (702, 298), "黑方储罐", False),
    ("h17", "storage", (678, 398), "紫球圣水瓶", False),
    ("h18", "storage", (898, 428), "紫球圣水瓶（原误标 town-hall，放大为紫球）", False),
    ("h19", "builder-hut", (1088, 388), "右侧橙色工匠棚", True),
    ("h20", None, (812, 112), "白塔紫座，类型不定", True),
    ("h21", "cannon", (872, 202), "红白链炮鼓，疑似加农炮", True),
    ("h22", "archer-tower", (832, 222), "灰白塔弓箭手，疑似箭塔", True),
    ("h23", None, (788, 308), "红熔岩盆，类型不定", True),
    # 中央
    ("h24", "clan-castle", (662, 308), "蓝色请求=部落城堡", True),
    ("h25", "storage", (722, 358), "金堆储罐", False),
    ("h26", "air-defense", (612, 392), "蓝色旋台双联炮，疑似防空", True),
    ("h27", None, (632, 428), "紫晶台，类型不定", True),
    ("h28", "mortar", (732, 428), "白筒迫击炮", True),
    # Q3
    ("h29", "collector", (158, 368), "紫滴圣水采集器", False),
    ("h30", "collector", (302, 452), "金币采集器", False),
    ("h31", "collector", (368, 468), "紫滴圣水采集器", False),
    ("h32", "storage", (532, 468), "紫球圣水瓶", False),
    ("h33", "storage", (392, 588), "黑块储罐", False),
    ("h34", "cannon", (412, 518), "橙色圆形炮体，疑似加农炮", True),
    ("h35", "archer-tower", (458, 528), "灰白塔弓箭手，疑似箭塔", True),
    # Q4
    ("h36", None, (762, 368), "深色塔，类型不定", True),
    ("h37", "mortar", (702, 428), "白筒迫击炮，疑似", True),
    ("h38", "storage", (802, 398), "紫球圣水瓶", False),
    ("h39", "collector", (802, 452), "黑油采集器", False),
    ("h40", "collector", (732, 478), "金币采集器", False),
    ("h41", "builder-hut", (762, 558), "红顶气球棚，工匠棚类", True),
    ("h42", None, (892, 428), "深色装置，类型不定", True),
    ("h43", "collector", (962, 358), "紫滴圣水采集器", False),
    ("h44", "collector", (662, 638), "紫滴圣水采集器", False),
    ("h45", "storage", (732, 658), "黑块储罐", False),
    # 城墙代表段（compartment 角点）
    ("w01", "wall", (300, 250), "西北墙段", False),
    ("w02", "wall", (560, 180), "北墙段", False),
    ("w03", "wall", (985, 255), "东北墙段", False),
    ("w04", "wall", (220, 470), "西南墙段", False),
    ("w05", "wall", (620, 560), "中南墙段", False),
    ("w06", "wall", (905, 430), "东南墙段", False),
]

buildings, ambiguous = [], []
for bid, typ, px, note, amb in ROWS:
    tx, ty = calib.px_to_tile(*px)
    entry = {
        "id": bid,
        "type": typ,
        "tile": [int(round(tx)), int(round(ty))],
        "size_tiles": 1 if typ in ("collector", "builder-hut", "wall", None) else 2,
        "foot_px": list(px),
        "foot_tile_raw": [round(tx, 3), round(ty, 3)],
        "note": note,
    }
    buildings.append(entry)
    if amb or typ is None:
        ambiguous.append({"id": bid, "field": "type", "reason": note})

out = {
    "name": "home_village_gold",
    "grid": 44,
    "source_image": "out/snap/_source/home_village.png",
    "annotator_note": "v2 人工看图逐栋标注（未参考检测结果）。家帧 home_village.png；四角沿用与引擎标签空间一致的旧 H，换算走 Calib.px_to_tile。类型 best-effort，看不清进 ambiguous；storage/collector/wall 照常标出，仅口径B排除。",
    "calib": {"n": 44, "H": human["H"]},
    "quad": human["quad"],
    "buildings": buildings,
    "ambiguous": ambiguous,
    "skipped": [],
}
dst = os.path.join(ROOT, "out/snap/gold/home_village_gold.json")
json.dump(out, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
for b in buildings:
    print(b["id"], b["type"], b["tile"], b["foot_px"], b["foot_tile_raw"])
print("total", len(buildings), "ambiguous", len(ambiguous))
