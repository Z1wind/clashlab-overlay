# -*- coding: utf-8 -*-
"""模板匹配检测尝试：用社区素材（assets/coc/buildings）在反投影阵图上做 NCC 匹配。"""
import json, os, sys
import numpy as np, cv2
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "out", "overlay", "_2d")
S = 24  # px per tile
TYPES = {"cannon": 3, "x-bow": 3, "town-hall": 4, "inferno-tower": 2, "air-defense": 3}
LEVELS = {"cannon": "level-16.png", "x-bow": "level-6.png", "town-hall": "level-13.png",
          "inferno-tower": "level-6.png", "air-defense": "level-10.png"}

def imread_u(p): return cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)

js = json.load(open(os.path.join(BASE, "out", "overlay", "_quad_calib", "summary.json"), encoding="utf-8"))
b = "03"
frame = imread_u(os.path.join(BASE, "bases", "th16", b, "base.png"))
H = np.array(js[b]["H"], np.float64)
lay = json.load(open(os.path.join(BASE, "bases", "th16", b, "layout.json"), encoding="utf-8"))
g = int(lay.get("grid", 44))
# 反投影整阵到 44*S 网格
K = H @ np.array([[1.0 / S, 0, 0], [0, 1.0 / S, 0], [0, 0, 1]])
warp = cv2.warpPerspective(frame, np.linalg.inv(K), (g * S, g * S), flags=cv2.INTER_LINEAR,
                           borderMode=cv2.BORDER_REPLICATE)
cv2.imencode(".png", warp)[1].tofile(os.path.join(OUT, "03_rectified.png"))
truth = {}
for bd in lay["buildings"]:
    truth.setdefault(bd["type"], []).append((float(bd["tile"][0]), float(bd["tile"][1])))
results = []
for t, k in TYPES.items():
    p = os.path.join(BASE, "assets", "coc", "buildings", t, LEVELS[t])
    if not os.path.exists(p):
        results.append({"type": t, "error": "sprite missing"})
        continue
    sp = imread_u(p)
    for scale in (1.0, 0.8, 1.2):
        side = int(k * S * scale)
        sp2 = cv2.resize(sp, (side, side), interpolation=cv2.INTER_AREA)
        res = cv2.matchTemplate(warp, sp2, cv2.TM_CCOEFF_NORMED)
        n_top = 6
        idx = np.dstack(np.unravel_index(np.argsort(res.ravel())[::-1][:n_top], res.shape))[0]
        peaks = [(float(x + side / 2.0) / S, float(y + side / 2.0) / S, float(res[y, x])) for y, x in idx]
        hits = 0
        for px, py, sc in peaks:
            for tx, ty in truth.get(t, []):
                if abs(px - tx) <= 1.5 and abs(py - ty) <= 1.5:
                    hits += 1
                    break
        results.append({"type": t, "scale": scale, "n_truth": len(truth.get(t, [])),
                        "top_peaks": [(round(a, 1), round(c, 1), round(s, 2)) for a, c, s in peaks],
                        "hits": hits})
json.dump(results, open(os.path.join(OUT, "template_probe.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for r in results:
    print(r["type"], "scale", r.get("scale"), "truth", r.get("n_truth"), "hits", r.get("hits"),
          "top3", r.get("top_peaks", [])[:3])
