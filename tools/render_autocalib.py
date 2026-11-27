# -*- coding: utf-8 -*-
"""渲染图自动标定：城墙（亮白）外缘极值 → 菱形四角；检查 GT 对齐。"""
import json, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
import cv2, numpy as np
from clashlab.geo import Calib

def wall_quad(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # 城墙：低饱和、亮（米白/亮白）
    m = cv2.inRange(hsv, (0, 0, 175), (180, 70, 255))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    ys, xs = np.nonzero(m)
    if len(xs) < 200:
        return None, 0
    # 用分位数避免水印/噪点
    left = [xs.min(), int(np.median(ys[xs <= xs.min() + 3]))]
    right = [xs.max(), int(np.median(ys[xs >= xs.max() - 3]))]
    top = [int(np.median(xs[ys <= ys.min() + 3])), ys.min()]
    bottom = [int(np.median(xs[ys >= ys.max() - 3])), ys.max()]
    # Calib 顺序：top, right, bottom, left
    return np.float32([top, right, bottom, left]), len(xs)

for ann_name, img_name in [("01_annotated.json","b01.jpg"),("03_annotated.json","b02.jpg"),
                           ("04_annotated.json","b03.jpg"),("05_annotated.json","b04.jpg"),
                           ("06_annotated.json","b05.jpg")]:
    img = cv2.imdecode(np.fromfile(BASE + "/android/assets/img/" + img_name, np.uint8), cv2.IMREAD_COLOR)
    quad, npx = wall_quad(img)
    print(img_name, "wall px", npx, "quad", None if quad is None else np.round(quad, 1).tolist())
    if quad is None:
        continue
    cal = Calib.from_quad(quad, n=44)
    ann = json.load(open(BASE + "/out/annotate/" + ann_name, encoding="utf-8"))
    vis = img.copy()
    for b in ann["buildings"]:
        x, y = b["tile"]; p = cal.tile_to_px(x + 0.5, y + 0.5)
        cv2.circle(vis, (int(p[0]), int(p[1])), 5, (0, 0, 255), 2)
    for k in range(0, 45, 4):
        a = cal.tile_to_px(k, 0); b2 = cal.tile_to_px(k, 44)
        cv2.line(vis, (int(a[0]), int(a[1])), (int(b2[0]), int(b2[1])), (255, 0, 255), 1)
        c = cal.tile_to_px(0, k); d = cal.tile_to_px(44, k)
        cv2.line(vis, (int(c[0]), int(c[1])), (int(d[0]), int(d[1])), (255, 0, 255), 1)
    out = BASE + "/out/layouts_src/wallgt_" + img_name.replace(".jpg", ".png")
    cv2.imencode(".png", vis)[1].tofile(out)
    json.dump({"quad": quad.tolist()}, open(BASE + "/out/layouts_src/quad_" + img_name.replace(".jpg", ".json"), "w"))
print("saved wallgt_*.png")
