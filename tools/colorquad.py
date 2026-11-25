# -*- coding: utf-8 -*-
"""用「基地内部颜色」分割出整块基地，再取四极角点作为 quad。"""
import json, os, sys
import numpy as np, cv2
sys.path.insert(0, r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat")
from clashlab.geo import Calib
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "out", "import")

def detect_quad(img):
    h, w = img.shape[:2]
    # 中心区域中位数颜色（基地地面）
    cx0, cx1 = int(w*0.30), int(w*0.70); cy0, cy1 = int(h*0.30), int(h*0.70)
    patch = img[cy0:cy1, cx0:cx1].reshape(-1, 3).astype(np.float32)
    med = np.median(patch, axis=0)
    dist = np.linalg.norm(img.astype(np.float32) - med[None, None, :], axis=2)
    m = (dist < 70).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((15, 15), np.uint8))
    n, lab, stats, cents = cv2.connectedComponentsWithStats(m, 8)
    if n <= 1: return None, 0
    # 选面积大、且质心靠近画面中心的分量
    best, bestscore = None, -1
    for i in range(1, n):
        area = stats[i, 4]
        d = np.linalg.norm(cents[i] - np.array([w/2, h/2]))
        score = area / (1.0 + d)
        if score > bestscore:
            best, bestscore = i, score
    comp = (lab == best).astype(np.uint8) * 255
    cnts, _ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    c = max(cnts, key=cv2.contourArea)
    hull = cv2.convexHull(c)
    pts = hull.reshape(-1, 2).astype(np.float32)
    s = pts.sum(axis=1); d = np.diff(pts, axis=1).ravel()
    top = pts[np.argmin(s)]; bottom = pts[np.argmax(s)]
    left = pts[np.argmin(d)]; right = pts[np.argmax(d)]
    quad = np.array([top, right, bottom, left], np.float32)
    return quad, stats[best, 4] / float(w * h)

for n in ("01", "03", "05"):
    img = cv2.imdecode(np.fromfile(os.path.join(BASE, "bases", "th16", n, "base.png"), np.uint8), cv2.IMREAD_COLOR)
    quad, ratio = detect_quad(img)
    print(n, "ratio=%.2f" % ratio if quad is not None else "FAIL", "quad=", np.round(quad,1).tolist() if quad is not None else None)
    if quad is None: continue
    vis = img.copy()
    calib = Calib.from_quad(quad, n=44)
    for i in range(45):
        cv2.line(vis, tuple(np.int32(calib.tile_to_px(i, 0))), tuple(np.int32(calib.tile_to_px(i, 44))), (0, 255, 0), 2)
        cv2.line(vis, tuple(np.int32(calib.tile_to_px(0, i))), tuple(np.int32(calib.tile_to_px(44, i))), (255, 128, 0), 2)
    cv2.imencode(".png", vis)[1].tofile(os.path.join(OUT, n + "_colorquad.png"))
