# -*- coding: utf-8 -*-
"""对比 b01 与 b06 同类建筑的裁剪，判断是否旋转/偏移。"""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab.geo import Calib
DL = os.path.join(os.path.expanduser("~"), "Downloads")
def crop_for(i, typ):
    d = json.load(open(os.path.join(DL, "annot_b%02d.json" % i), encoding="utf-8"))
    img = cv2.imdecode(np.fromfile(os.path.join(BASE, "android", "assets", "img", "b%02d.jpg" % i), np.uint8), cv2.IMREAD_COLOR)
    wn, hn = d["image_size"]; quad = np.float32([[u*wn, v*hn] for u, v in d["corners_norm"]])
    cal = Calib.from_quad(quad, n=44)
    b = next(x for x in d["buildings"] if x["type"] == typ)
    x, y = b["tile"]; side = 4
    x0 = max(0, x-1); y0 = max(0, y-1); x1 = min(44, x0+side); y1 = min(44, y0+side)
    p = [cal.tile_to_px(x0,y0), cal.tile_to_px(x1,y0), cal.tile_to_px(x1,y1), cal.tile_to_px(x0,y1)]
    H = cv2.getPerspectiveTransform(np.float32(p), np.float32([[0,0],[96,0],[96,96],[0,96]]))
    return cv2.warpPerspective(img, H, (96,96)), b["tile"]
rows = []
for typ in ("town-hall", "eagle-artillery", "air-defense", "x-bow"):
    tiles = []
    crops = []
    for i in (1, 6):
        try:
            c, t = crop_for(i, typ); crops.append(c); tiles.append(t)
        except StopIteration:
            crops.append(np.zeros((96,96,3), np.uint8)); tiles.append(None)
    row = np.hstack([cv2.copyMakeBorder(c, 4,4,4,4, cv2.BORDER_CONSTANT, value=(40,40,40)) for c in crops])
    rows.append(row)
    print(typ, "b01 tile", tiles[0], "b06 tile", tiles[1])
canvas = np.vstack(rows)
cv2.imencode(".png", canvas)[1].tofile(os.path.join(BASE, "out", "apk_qa", "crop_compare_b01_b06.png"))
print("saved crop_compare_b01_b06.png", canvas.shape)
