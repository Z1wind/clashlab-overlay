# -*- coding: utf-8 -*-
"""尝试自动检测站图的基地四边形（用于修正 quad）。"""
import json, os, sys
import numpy as np, cv2
sys.path.insert(0, r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat")
from clashlab.geo import Calib
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "out", "import")
os.makedirs(OUT, exist_ok=True)

def detect(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    # 基地地面：亮、低到中饱和（sand/grass），排除暗背景
    m = ((v > 95) & (v < 245) & (s > 25)).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((31, 31), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((21, 21), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    if n <= 1:
        return None
    bi = max(range(1, n), key=lambda i: stats[i, 4])
    comp = (lab == bi).astype(np.uint8) * 255
    cnts, _ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    c = max(cnts, key=cv2.contourArea)
    rect = cv2.minAreaRect(c)
    box = cv2.boxPoints(rect).astype(np.float32)
    return box, float(stats[bi, 4])

for n in ("01", "03", "05"):
    img = cv2.imdecode(np.fromfile(os.path.join(BASE, "bases", "th16", n, "base.png"), np.uint8), cv2.IMREAD_COLOR)
    res = detect(img)
    if res is None:
        print(n, "detect FAIL"); continue
    box, area = res
    print(n, "area_pct=%.1f%%" % (100.0 * area / (img.shape[0] * img.shape[1])), "box=", np.round(box, 1).tolist())
    vis = img.copy()
    cv2.drawContours(vis, [np.int32(box)], -1, (0, 255, 255), 4)
    cv2.imencode(".png", vis)[1].tofile(os.path.join(OUT, n + "_autoquad.png"))
