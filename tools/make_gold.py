# -*- coding: utf-8 -*-
"""gold 真值作者脚本：人工看图记录的脚点像素表 -> geo.Calib.px_to_tile 换算 -> gold JSON。

坐标换算唯一入口：clashlab.geo.Calib（from_quad 构造，px_to_tile 换算），不自造公式。
人工工作 = 下面 FOOT 表里的像素脚点与类型判断；脚本只做换算与落盘。

用法：python tools/make_gold.py
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from clashlab.geo import Calib, order_diamond

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = "out/snap/_source/village.png"
OUT = "out/snap/gold/village_gold.json"

# 人工标定四角（上、右、下、左，像素）；由 grid_overlay 目视对齐村庄后选定。
QUAD = [[640.0, 140.0], [1100.0, 390.0], [590.0, 675.0], [315.0, 385.0]]

# 人工脚点表：id, 脚点像素(x,y), type(可空), 尺寸格, 视觉备注
# type=None 表示类型无法可靠判定，进 ambiguous；storage/collector 必须照常标。
FOOTS = [
    ("g01", (352, 362), "builder-hut", 1, "左侧小屋（工匠棚类），素材库无此类"),
    ("g02", (432, 368), None, 3, "橙色主体建筑（锤旗/工坊外观），类型不定"),
    ("g03", (462, 438), None, 2, "金蓝多镜筒装置，类型不定"),
    ("g04", (520, 362), None, 2, "红顶塔楼（骷髅墙旁），类型不定"),
    ("g05", (618, 258), "collector", 2, "顶部木台带绿树（采集器类），素材库缺 collector"),
    ("g06", (700, 300), "inferno-tower", 2, "圆形红光鼓形塔，疑似地狱塔，类型存疑",),
    ("g07", (748, 238), "builder-hut", 1, "右上木屋（工匠棚类），素材库无此类"),
    ("g08", (592, 358), None, 2, "旋转平台小炮，类型不定"),
    ("g09", (700, 382), None, 2, "六边形火焰装置，类型不定"),
    ("g10", (762, 332), None, 2, "双管炮体，类型不定"),
    ("g11", (772, 368), None, 2, "红顶塔楼，类型不定"),
    ("g12", (700, 418), "wizard-tower", 2, "蓝焰宝珠塔楼，疑似法师塔，类型存疑"),
    ("g13", (632, 462), "collector", 2, "中部木台带粉树（采集器类），素材库缺 collector"),
    ("g14", (768, 465), "builder-hut", 1, "右侧生火木屋（工匠棚类），素材库无此类"),
    ("g15", (792, 398), "storage", 3, "金色储罐（资源仓），素材库缺 storage"),
    ("g16", (856, 295), None, 2, "紫罩圆顶，类型不定"),
    ("g17", (955, 345), None, 3, "橙色机器人，类型不定"),
    ("g18", (1005, 350), None, 1, "小型方箱，类型不定"),
    ("g19", (830, 388), "storage", 3, "敞开金箱（资源仓），素材库缺 storage"),
]

# 看清但不入库的条目（陷阱/装饰/标定时落在网格外），写进 skipped 供复核
SKIPPED = [
    {"px": [455, 258], "reason": "钟楼（21小时20分），落在标定网格西缘外，未纳入"},
    {"px": [585, 195], "reason": "顶部火盆陷阱/装饰，非建筑"},
    {"px": [690, 190], "reason": "顶部火盆陷阱/装饰，非建筑"},
    {"px": [640, 615], "reason": "底部火盆陷阱/装饰，非建筑"},
    {"px": [540, 628], "reason": "木箱装饰，非建筑"},
]


def main():
    quad = order_diamond(np.array(QUAD, dtype=np.float32))
    calib = Calib.from_quad(quad, n=44)
    buildings = []
    ambiguous = []
    for bid, (px, py), btype, size, note in FOOTS:
        gx, gy = calib.px_to_tile(px, py)
        tile = [int(round(gx)), int(round(gy))]
        entry = {
            "id": bid,
            "type": btype,
            "tile": tile,
            "size_tiles": size,
            "foot_px": [px, py],
            "foot_tile_raw": [round(gx, 3), round(gy, 3)],
            "note": note,
        }
        buildings.append(entry)
        if btype is None or "存疑" in note or "不定" in note:
            ambiguous.append({"id": bid, "field": "type", "reason": note})

    gold = {
        "name": "village_gold",
        "grid": 44,
        "source_image": SRC,
        "annotator_note": (
            "人工看图逐栋标注（未参考任何检测结果）。ADB 离线，源图为既有真实帧复制；"
            "标定四角由 grid_overlay 目视对齐后选定，换算走 clashlab.geo.Calib.px_to_tile。"
            "夜间/洞穴色调，多数建筑类型无法可靠辨认，类型存疑者进 ambiguous，不瞎猜。"
        ),
        "calib": calib.to_dict(),
        "quad": [[float(x), float(y)] for x, y in quad],
        "buildings": buildings,
        "ambiguous": ambiguous,
        "skipped": SKIPPED,
    }
    os.makedirs(os.path.dirname(os.path.join(ROOT, OUT)), exist_ok=True)
    with open(os.path.join(ROOT, OUT), "w", encoding="utf-8") as f:
        json.dump(gold, f, ensure_ascii=False, indent=2)
    print(f"wrote {OUT}: {len(buildings)} buildings, {len(ambiguous)} ambiguous")


if __name__ == "__main__":
    main()
