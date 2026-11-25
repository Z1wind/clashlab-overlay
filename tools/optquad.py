# -*- coding: utf-8 -*-
"""用已知墙格自动微调 quad：优化四角，使墙格中心落在「石墙像素」上。"""
import json, os, re, sys
import numpy as np, cv2
from scipy.optimize import minimize
sys.path.insert(0, r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat")
from clashlab.geo import Calib
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "out", "import")
QUAD_RE = re.compile(r"quad\s*=\s*\[\[[^\]]+\](?:\s*,\s*\[[^\]]+\]){3,}\]")

def load(n):
    lay = json.load(open(os.path.join(BASE, "bases", "th16", n, "layout.json"), encoding="utf-8"))
    m = QUAD_RE.search(lay.get("note") or "")
    quad = np.array(json.loads(m.group(0).split("=", 1)[1]), np.float64) if m else None
    img = cv2.imdecode(np.fromfile(os.path.join(BASE, "bases", "th16", n, "base.png"), np.uint8), cv2.IMREAD_COLOR)
    return lay, quad, img

def wall_score(img, quad, walls, n=44):
    calib = Calib.from_quad(quad.astype(np.float32), n=n)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    s = hsv[..., 1].astype(np.float32) / 255.0
    v = hsv[..., 2].astype(np.float32) / 255.0
    wallness = (1.0 - s) * v  # 石墙：低饱和、较亮
    vals = []
    H, W = wallness.shape
    for (x, y) in walls:
        px, py = calib.tile_to_px(x + 0.5, y + 0.5)
        ix, iy = int(round(px)), int(round(py))
        if 0 <= ix < W and 0 <= iy < H:
            vals.append(wallness[max(0,iy-1):iy+2, max(0,ix-1):ix+2].max())
    return float(np.mean(vals)) if vals else 0.0

for n in ("01", "03", "05"):
    lay, quad0, img = load(n)
    walls = lay.get("walls") or []
    base_score = wall_score(img, quad0, walls)
    def obj(p):
        return -wall_score(img, p.reshape(4, 2), walls)
    best = minimize(obj, quad0.ravel(), method="Nelder-Mead",
                    options={"maxiter": 600, "xatol": 0.5, "fatol": 1e-4})
    quad1 = best.x.reshape(4, 2)
    print("%s walls=%d score %.4f -> %.4f | quad0=%s | quad1=%s" % (
        n, len(walls), base_score, -best.fun, np.round(quad0, 1).tolist(), np.round(quad1, 1).tolist()))
    vis = img.copy()
    calib = Calib.from_quad(quad1.astype(np.float32), n=44)
    for i in range(45):
        cv2.line(vis, tuple(np.int32(calib.tile_to_px(i, 0))), tuple(np.int32(calib.tile_to_px(i, 44))), (0, 255, 0), 1)
        cv2.line(vis, tuple(np.int32(calib.tile_to_px(0, i))), tuple(np.int32(calib.tile_to_px(44, i))), (255, 128, 0), 1)
    cv2.imencode(".png", vis)[1].tofile(os.path.join(OUT, n + "_optquad.png"))
