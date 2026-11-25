# -*- coding: utf-8 -*-
"""home_village gold 作者脚本：人工脚点表 -> geo.Calib.px_to_tile -> home_village_gold.json。

夜世界 village_gold.json 仅作管线自检，不参与正式结论。
用法：python tools/make_gold_home.py
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from clashlab.geo import Calib, order_diamond

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = "out/snap/_source/home_village.png"
OUT = "out/snap/gold/home_village_gold.json"

# 人工标定四角（上、右、下、左，像素）；覆盖全部被标建筑，存 gold.calib 可复算。
QUAD = [[489.0, 0.0], [1260.0, 300.0], [600.0, 720.0], [13.0, 284.0]]

# id, 脚点(x,y), type(可空), size_tiles, 备注；best-effort 类型在备注标“存疑”
FOOTS = [
    ("h01", (200, 185), "builder-hut", 1, "左侧工匠棚，素材库无此类"),
    ("h02", (335, 145), "army-camp", 3, "帐篷训练营，素材库无此类"),
    ("h03", (385, 215), "collector", 2, "圣水采集器（紫滴），素材库缺 collector"),
    ("h04", (305, 255), "collector", 2, "金币采集器（金币），素材库缺 collector"),
    ("h05", (435, 255), "storage", 3, "圣水瓶（紫球95），素材库缺 storage"),
    ("h06", (365, 305), "archer-tower", 2, "白塔紫座，疑似箭塔，类型存疑"),
    ("h07", (455, 235), "cannon", 2, "红鼓炮体，疑似加农炮，类型存疑"),
    ("h08", (455, 155), "storage", 3, "金币储罐，素材库缺 storage"),
    ("h09", (665, 185), "x-bow", 3, "深色弩塔，疑似 X 连弩，类型存疑"),
    ("h10", (855, 145), "archer-tower", 2, "白塔，疑似箭塔，类型存疑"),
    ("h11", (775, 235), "storage", 3, "深色储罐，素材库缺 storage"),
    ("h12", (665, 235), "cannon", 2, "带计时炮体，疑似加农炮，类型存疑"),
    ("h13", (705, 305), "storage", 3, "黑立方圣油罐，素材库缺 storage"),
    ("h14", (835, 265), "cannon", 2, "红鼓炮体，疑似加农炮，类型存疑"),
    ("h15", (875, 305), "archer-tower", 2, "白塔，疑似箭塔，类型存疑"),
    ("h16", (565, 265), "storage", 3, "金堆储罐，素材库缺 storage"),
    ("h17", (1015, 335), "builder-hut", 1, "右侧橙色工匠棚，素材库无此类"),
    ("h18", (255, 365), "collector", 2, "圣水采集器（紫滴），素材库缺 collector"),
    ("h19", (365, 455), "storage", 3, "黑箱储罐，素材库缺 storage"),
    ("h20", (365, 545), "collector", 2, "圣水采集器，素材库缺 collector"),
    ("h21", (405, 305), "archer-tower", 2, "深色高塔，疑似箭塔，类型存疑"),
    ("h22", (565, 305), "x-bow", 3, "深色弩塔，疑似 X 连弩，类型存疑"),
    ("h23", (665, 335), "clan-castle", 3, "蓝顶请求=部落城堡，素材库无此类"),
    ("h24", (765, 305), "storage", 3, "金堆储罐，素材库缺 storage"),
    ("h25", (625, 405), "hidden-tesla", 2, "蓝台装置，疑似特斯拉，类型存疑"),
    ("h26", (765, 435), "mortar", 3, "白筒迫击炮，类型存疑"),
    ("h27", (835, 475), "archer-tower", 2, "白塔，疑似箭塔，类型存疑"),
    ("h28", (565, 485), "storage", 3, "紫球圣水瓶，素材库缺 storage"),
    ("h29", (665, 505), "cannon", 2, "炮体，疑似加农炮，类型存疑"),
    ("h30", (700, 560), "archer-tower", 2, "白塔紫座，疑似箭塔，类型存疑"),
    ("h31", (760, 530), "collector", 2, "金币采集器，素材库缺 collector"),
    ("h32", (830, 510), "cannon", 2, "炮体，疑似加农炮，类型存疑"),
    ("h33", (900, 500), "storage", 3, "深色储罐，素材库缺 storage"),
]

SKIPPED = [
    {"px": [305, 525], "reason": "金币采集器，落在标定网格南缘外，未纳入"},
    {"px": [1010, 470], "reason": "炮体，落在标定网格东缘外，未纳入"},
    {"px": [960, 250], "reason": "右侧炮体，类型不定且贴边，未纳入"},
    {"px": [590, 125], "reason": "顶部小棚/陷阱，非主体建筑"},
    {"px": [765, 155], "reason": "棕色建筑，类型不定，未纳入"},
    {"px": [960, 380], "reason": "飞行龙雕饰，非建筑"},
]


def main():
    quad = order_diamond(np.array(QUAD, dtype=np.float32))
    calib = Calib.from_quad(quad, n=44)
    buildings = []
    ambiguous = []
    for bid, (px, py), btype, size, note in FOOTS:
        gx, gy = calib.px_to_tile(px, py)
        tile = [int(round(gx)), int(round(gy))]
        buildings.append({
            "id": bid, "type": btype, "tile": tile, "size_tiles": size,
            "foot_px": [px, py], "foot_tile_raw": [round(gx, 3), round(gy, 3)],
            "note": note,
        })
        if btype is None or "存疑" in note or "不定" in note or "无此类" in note or "缺 " in note:
            ambiguous.append({"id": bid, "field": "type", "reason": note})

    gold = {
        "name": "home_village_gold",
        "grid": 44,
        "source_image": SRC,
        "annotator_note": (
            "人工看图逐栋标注（未参考任何检测结果）。家乡帧 home_village.png（ADB 实抓，无弹窗无面板遮挡）。"
            "标定四角由目视覆盖选定，换算走 clashlab.geo.Calib.px_to_tile（44x44）。"
            "多数防御类型在该分辨率下只能 best-effort，存疑者进 ambiguous，不瞎猜；"
            "storage/collector 照常标出，仅在统计口径B中排除。"
        ),
        "calib": calib.to_dict(),
        "quad": [[float(x), float(y)] for x, y in quad],
        "buildings": buildings,
        "ambiguous": ambiguous,
        "skipped": SKIPPED,
    }
    os.makedirs(os.path.join(ROOT, os.path.dirname(OUT)), exist_ok=True)
    with open(os.path.join(ROOT, OUT), "w", encoding="utf-8") as f:
        json.dump(gold, f, ensure_ascii=False, indent=2)
    print(f"wrote {OUT}: {len(buildings)} buildings, {len(ambiguous)} ambiguous")


if __name__ == "__main__":
    main()
