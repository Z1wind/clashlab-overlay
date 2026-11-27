# -*- coding: utf-8 -*-
"""尺度感知锚点匹配：按 footprint 推算 sprite 显示尺寸，只在预测位置附近搜索。"""
import glob, json, os, random, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
import cv2, numpy as np
from clashlab.geo import Calib
from clashlab.assets import STATS
SPR = os.path.join(BASE, "assets", "clashking", "buildings")
MAP = {"air-defense":"air_defense","x-bow":"x-bow","builder-hut":"builder's_hut",
       "multi-archer-tower":"multi-archer_tower","multi-gear-tower":"multi-gear_tower"}
def sprite(t):
    d = os.path.join(SPR, MAP.get(t, t.replace("-", "_")))
    if not os.path.isdir(d): return None
    fs = glob.glob(d + "/*.webp") + glob.glob(d + "/*.png")
    if not fs: return None
    fs.sort(key=lambda f: int(re.search(r"level_(\d+)", f).group(1)) if re.search(r"level_(\d+)", f) else 0)
    return cv2.imdecode(np.fromfile(fs[-1], np.uint8), cv2.IMREAD_UNCHANGED)
ann = json.load(open(os.path.join(BASE, "out", "annotate", "01_annotated.json"), encoding="utf-8"))
img = cv2.imdecode(np.fromfile(os.path.join(BASE, "android", "assets", "img", "b01.jpg"), np.uint8), cv2.IMREAD_COLOR)
H, W = img.shape[:2]
m = re.search(r"quad=\[\[([^\]]+)\],\[([^\]]+)\],\[([^\]]+)\],\[([^\]]+)\]\]", ann.get("note") or "")
q = np.array([[float(v) for v in g.split(",")] for g in m.groups()], np.float32) * (W / 2622.0)
cal0 = Calib.from_quad(q, n=44)
# 估算每格像素
px_per_tile = float(np.linalg.norm(q[1] - q[0])) / 44.0
print("px_per_tile", round(px_per_tile, 2))
anchors = []; tried = 0
for b in ann["buildings"]:
    t = b["type"]; spr = sprite(t)
    if spr is None: continue
    tried += 1
    size = int((STATS.get(t) or {}).get("size") or 2)
    sx, sy = int(b["tile"][0] + size / 2.0), int(b["tile"][1] + size / 2.0)
    px, py = cal0.tile_to_px(sx, sy)
    R = int(px_per_tile * 2.2)
    x0, y0 = max(0, int(px - R)), max(0, int(py - R))
    x1, y1 = min(W, int(px + R)), min(H, int(py + R))
    roi = img[y0:y1, x0:x1]
    if roi.size == 0: continue
    best = None
    for mul in (0.7, 0.85, 1.0, 1.15, 1.3):
        target_w = size * px_per_tile * mul
        sc = target_w / spr.shape[1]
        tw = max(8, int(spr.shape[1] * sc)); th = max(8, int(spr.shape[0] * sc))
        if tw >= roi.shape[1] or th >= roi.shape[0]: continue
        tpl = cv2.resize(spr[:, :, :3], (tw, th), interpolation=cv2.INTER_AREA)
        msk = cv2.resize(spr[:, :, 3], (tw, th), interpolation=cv2.INTER_NEAREST)
        res = cv2.matchTemplate(roi, tpl, cv2.TM_CCORR_NORMED, mask=msk)
        res = np.nan_to_num(res, nan=0.0, posinf=0.0, neginf=0.0)
        _, mx, _, ml = cv2.minMaxLoc(res)
        if best is None or mx > best[0]:
            best = (float(mx), x0 + ml[0] + tw / 2.0, y0 + ml[1] + th / 2.0)
    if best and best[0] > 0.80:
        anchors.append((sx, sy, best[1], best[2], best[0], t))
print("tried", tried, "anchors", len(anchors))
# RANSAC
def ransac(anchors, iters=2000, tol=8.0):
    src = np.array([[a[0], a[1]] for a in anchors], np.float32)
    dst = np.array([[a[2], a[3]] for a in anchors], np.float32)
    rng = random.Random(7); best = None
    for _ in range(iters):
        idx = rng.sample(range(len(anchors)), 4)
        Hm, _ = cv2.findHomography(src[idx], dst[idx], 0)
        if Hm is None: continue
        proj = cv2.perspectiveTransform(src.reshape(-1, 1, 2), Hm).reshape(-1, 2)
        err = np.linalg.norm(proj - dst, axis=1)
        inl = err < tol
        if best is None or inl.sum() > best.sum(): best = inl
    if best is None or best.sum() < 6: return None, []
    Hm, _ = cv2.findHomography(src[best], dst[best], 0)
    return Hm, [a for a, k in zip(anchors, best) if k]
Hm, inl = ransac(anchors)
print("inliers", len(inl))
if Hm is not None:
    quad_new = np.array([cv2.perspectiveTransform(np.float32([[[0,0]]]), Hm)[0][0],
                         cv2.perspectiveTransform(np.float32([[[44,0]]]), Hm)[0][0],
                         cv2.perspectiveTransform(np.float32([[[44,44]]]), Hm)[0][0],
                         cv2.perspectiveTransform(np.float32([[[0,44]]]), Hm)[0][0]], np.float32)
    print("new quad", np.round(quad_new, 1).tolist())
    cal = Calib.from_quad(quad_new, n=44)
    vis = img.copy()
    for b in ann["buildings"]:
        size = int((STATS.get(b["type"]) or {}).get("size") or 2)
        p = cal.tile_to_px(b["tile"][0] + size / 2, b["tile"][1] + size / 2)
        cv2.circle(vis, (int(p[0]), int(p[1])), 6, (0, 0, 255), 2)
    for a in inl:
        cv2.circle(vis, (int(a[2]), int(a[3])), 3, (0, 255, 0), -1)
    cv2.imencode(".png", vis)[1].tofile(os.path.join(BASE, "out", "layouts_src", "scale_anchor_b01.png"))
    json.dump({"quad": quad_new.tolist(), "inliers": len(inl), "anchors": len(anchors)},
              open(os.path.join(BASE, "out", "layouts_src", "scale_anchor_b01.json"), "w"), indent=1)
    print("saved scale_anchor_b01.png")
else:
    print("RANSAC failed")
