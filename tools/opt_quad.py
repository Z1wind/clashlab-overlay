# -*- coding: utf-8 -*-
"""优化 quad（缩放/旋转/平移），让 GT 建筑中心落在高纹理/高饱和区域。"""
import json, math, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
import cv2, numpy as np
from clashlab.geo import Calib
ann = json.load(open(BASE + "/out/annotate/01_annotated.json", encoding="utf-8"))
img = cv2.imdecode(np.fromfile(BASE + "/android/assets/img/b01.jpg", np.uint8), cv2.IMREAD_COLOR)
h, w = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV); gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
lap = cv2.Laplacian(gray, cv2.CV_32F); var = cv2.blur(lap * lap, (15, 15))
sat = hsv[:, :, 1].astype(np.float32)
def sc_of(quad):
    cal = Calib.from_quad(np.float32(quad), n=44)
    s = 0.0
    for b in ann["buildings"]:
        x, y = b["tile"]; p = cal.tile_to_px(x + 0.5, y + 0.5)
        xi, yi = int(round(p[0])), int(round(p[1]))
        if 0 <= xi < w and 0 <= yi < h:
            s += min(var[yi, xi], 500.0) + 0.3 * sat[yi, xi]
    return s
m = re.search(r"quad=\[\[([^\]]+)\],\[([^\]]+)\],\[([^\]]+)\],\[([^\]]+)\]\]", ann["note"])
q0 = np.array([[float(v) for v in g.split(",")] for g in m.groups()], np.float32) * (w / 2622.0)
c = q0.mean(axis=0)
best = None
for s in np.arange(0.80, 1.31, 0.05):
    for deg in (-4, -2, 0, 2, 4):
        a = math.radians(deg); ca, sa = math.cos(a), math.sin(a)
        q = (q0 - c) @ np.array([[ca, sa], [-sa, ca]], np.float32) * s + c
        for dx in range(-60, 61, 20):
            for dy in range(-60, 61, 20):
                qq = q + np.array([dx, dy], np.float32)
                sc = sc_of(qq)
                if best is None or sc > best[0]:
                    best = (sc, (s, deg, dx, dy), qq.copy())
print("best score", round(best[0], 1), "params", best[1])
print("quad", np.round(best[2], 1).tolist())
json.dump({"quad": best[2].tolist(), "params": best[1]}, open(BASE + "/out/layouts_src/opt_quad_b01.json", "w"))
cal = Calib.from_quad(best[2], n=44)
vis = img.copy()
for b in ann["buildings"]:
    x, y = b["tile"]; p = cal.tile_to_px(x + 0.5, y + 0.5)
    cv2.circle(vis, (int(p[0]), int(p[1])), 5, (0, 0, 255), 2)
for k in range(0, 45, 4):
    a1 = cal.tile_to_px(k, 0); a2 = cal.tile_to_px(k, 44); b1 = cal.tile_to_px(0, k); b2 = cal.tile_to_px(44, k)
    cv2.line(vis, (int(a1[0]), int(a1[1])), (int(a2[0]), int(a2[1])), (255, 0, 255), 1)
    cv2.line(vis, (int(b1[0]), int(b1[1])), (int(b2[0]), int(b2[1])), (255, 0, 255), 1)
cv2.imencode(".png", vis)[1].tofile(BASE + "/out/layouts_src/opt_gt_b01.png")
print("saved opt_gt_b01.png")
