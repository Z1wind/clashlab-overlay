# -*- coding: utf-8 -*-
"""用近似 quad + 门控候选，按 1 格边距裁 96x96 拼图（容忍标定偏差）。"""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab import auto_candidates as ac
from clashlab.geo import Calib
import cv2, numpy as np
IMG = os.path.join(BASE, "out", "live", "hires", "coc_193842_6.png")
QUAD = np.float32([[175, 610], [955, 20], [1850, 585], [960, 950]])
img = cv2.imdecode(np.fromfile(IMG, np.uint8), cv2.IMREAD_COLOR)
cal = Calib.from_quad(QUAD, n=44)
r = ac.candidates(IMG, QUAD.tolist(), max_n=90, gate_only=True, gate_threshold=0.70, recall=True)
items = r.get("items") or []
print("candidates:", len(items))
S, SCALE, PAD, COLS, ROWS = 96, 3, 26, 6, 4
PER = COLS * ROWS
os.makedirs(os.path.join(BASE, "out", "labels"), exist_ok=True)
for b in range((len(items) + PER - 1) // PER):
    canvas = np.full((ROWS * (S*SCALE + PAD) + PAD, COLS * (S*SCALE + PAD) + PAD, 3), 32, np.uint8)
    for k in range(PER):
        i = b * PER + k
        if i >= len(items):
            break
        it = items[i]; x, y = it["tile"]; size = it["size"]
        m = 1
        x0 = max(0, x - m); y0 = max(0, y - m)
        x1 = min(44, x + size + m); y1 = min(44, y + size + m)
        p2 = [cal.tile_to_px(x0,y0), cal.tile_to_px(x1,y0), cal.tile_to_px(x1,y1), cal.tile_to_px(x0,y1)]
        H = cv2.getPerspectiveTransform(np.float32(p2), np.float32([[0,0],[S,0],[S,S],[0,S]]))
        crop = cv2.warpPerspective(img, H, (S, S), flags=cv2.INTER_AREA)
        crop = cv2.resize(crop, (S*SCALE, S*SCALE), interpolation=cv2.INTER_CUBIC)
        rr, cc = k // COLS, k % COLS
        y_ = PAD + rr * (S*SCALE + PAD); x_ = PAD + cc * (S*SCALE + PAD)
        canvas[y_:y_+S*SCALE, x_:x_+S*SCALE] = crop
        cv2.putText(canvas, "#%d(%dx%d)" % (i+1, it["tile"][0], it["tile"][1]), (x_, y_-6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 220, 255), 1)
    out = os.path.join(BASE, "out", "labels", "hm2_%d.png" % (b+1))
    cv2.imencode(".png", canvas)[1].tofile(out)
    print("saved", out)
json.dump({"image": IMG, "quad": QUAD.tolist(), "items": items},
          open(os.path.join(BASE, "out", "labels", "hm2_candidates.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
