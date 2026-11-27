# -*- coding: utf-8 -*-
"""用局部模板匹配取锚点 → Calib.from_anchors 重建渲染图标定。"""
import glob, json, os, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
import cv2, numpy as np
from clashlab.geo import Calib
from clashlab.assets import STATS
ANN = BASE + "/out/annotate/01_annotated.json"
IMG = BASE + "/android/assets/img/b01.jpg"
SPR = BASE + "/assets/clashking/buildings"
ann = json.load(open(ANN, encoding="utf-8"))
img = cv2.imdecode(np.fromfile(IMG, np.uint8), cv2.IMREAD_COLOR)
h, w = img.shape[:2]
m = re.search(r"quad=\[\[([^\]]+)\],\[([^\]]+)\],\[([^\]]+)\],\[([^\]]+)\]\]", ann["note"])
q = np.array([[float(v) for v in g.split(",")] for g in m.groups()], np.float32) * (w / 2622.0)
cal0 = Calib.from_quad(q, n=44)
MAP = {"air-defense":"air_defense","x-bow":"x-bow","builder-hut":"builder's_hut",
       "multi-archer-tower":"multi-archer_tower","multi-gear-tower":"multi-gear_tower"}
def sprite(t):
    d = os.path.join(SPR, MAP.get(t, t.replace("-", "_")))
    if not os.path.isdir(d): return None
    fs = glob.glob(d + "/*.webp") + glob.glob(d + "/*.png")
    if not fs: return None
    fs.sort(key=lambda f: int(re.search(r"level_(\d+)", f).group(1)) if re.search(r"level_(\d+)", f) else 0)
    return cv2.imdecode(np.fromfile(fs[-1], np.uint8), cv2.IMREAD_UNCHANGED)
types = ["town-hall", "monolith", "eagle-artillery", "scattershot", "x-bow", "inferno-tower", "clan-castle"]
anchors = []
for t in types:
    spr = sprite(t)
    if spr is None: 
        print("no sprite", t); continue
    for b in ann["buildings"]:
        if b["type"] != t: continue
        sx = int((STATS.get(t) or {}).get("size") or 2)
        gx, gy = b["tile"][0] + sx/2, b["tile"][1] + sx/2
        px, py = cal0.tile_to_px(gx, gy)
        R = 140
        x0, y0 = max(0, int(px - R)), max(0, int(py - R))
        x1, y1 = min(w, int(px + R)), min(h, int(py + R))
        roi = img[y0:y1, x0:x1]
        best = None
        for sc in (0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
            tw = max(8, int(spr.shape[1]*sc)); th = max(8, int(spr.shape[0]*sc))
            if tw >= roi.shape[1] or th >= roi.shape[0]: continue
            tpl = cv2.resize(spr[:, :, :3], (tw, th), interpolation=cv2.INTER_AREA)
            msk = cv2.resize(spr[:, :, 3], (tw, th), interpolation=cv2.INTER_NEAREST)
            res = cv2.matchTemplate(roi, tpl, cv2.TM_CCORR_NORMED, mask=msk)
            res = np.nan_to_num(res, nan=0.0, posinf=0.0, neginf=0.0)
            _, mx, _, ml = cv2.minMaxLoc(res)
            if best is None or mx > best[0]:
                best = (float(mx), x0 + ml[0] + tw/2.0, y0 + ml[1] + th/2.0, sc)
        print(t, "at tile", b["tile"], "pred", (round(px), round(py)), "best", None if not best else (round(best[0],3), round(best[1]), round(best[2]), best[3]))
        if best and best[0] > 0.55:
            anchors.append((gx, gy, best[1], best[2]))
print("anchors:", len(anchors), anchors[:5])
if len(anchors) >= 4:
    cal = Calib.from_anchors(anchors, n=44)
    vis = img.copy()
    for b in ann["buildings"]:
        sx = int((STATS.get(b["type"]) or {}).get("size") or 2)
        p = cal.tile_to_px(b["tile"][0] + sx/2, b["tile"][1] + sx/2)
        cv2.circle(vis, (int(p[0]), int(p[1])), 5, (0, 0, 255), 2)
    cv2.imencode(".png", vis)[1].tofile(BASE + "/out/layouts_src/anchor_gt_b01.png")
    print("saved anchor_gt_b01.png")
