# -*- coding: utf-8 -*-
"""高分辨率基地截图：自动标定 + 门控候选 + 拼图（供 AI 标类型）。"""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab import calib as C, auto_candidates as ac
from clashlab.geo import Calib
import cv2, numpy as np
IMG = os.path.join(BASE, "out", "live", "hires", "coc_193842_6.png")
img = cv2.imdecode(np.fromfile(IMG, np.uint8), cv2.IMREAD_COLOR)
print("img:", None if img is None else img.shape)
cal, meta = C.detect_village_quad(img, grid_n=44)
print("calib method:", meta.get("method"), "quad:", meta.get("quad"), "area_ratio:", meta.get("area_ratio"))
if cal is None:
    raise SystemExit("calib failed")
quad = meta["quad"]
r = ac.candidates(IMG, quad, max_n=90, gate_only=True, gate_threshold=0.70, recall=True)
items = r.get("items") or []
print("candidates:", len(items), "| gate:", r.get("gate_used"), r.get("gated_counts"))
os.makedirs(os.path.join(BASE, "out", "labels"), exist_ok=True)
S, SCALE, PAD, COLS, ROWS = 96, 3, 26, 6, 4
PER = COLS * ROWS
for b in range((len(items) + PER - 1) // PER):
    canvas = np.full((ROWS * (S*SCALE + PAD) + PAD, COLS * (S*SCALE + PAD) + PAD, 3), 32, np.uint8)
    for k in range(PER):
        i = b * PER + k
        if i >= len(items):
            break
        it = items[i]; x, y = it["tile"]; size = it["size"]
        p2 = [cal.tile_to_px(x,y), cal.tile_to_px(x+size,y), cal.tile_to_px(x+size,y+size), cal.tile_to_px(x,y+size)]
        H = cv2.getPerspectiveTransform(np.float32(p2), np.float32([[0,0],[S,0],[S,S],[0,S]]))
        crop = cv2.warpPerspective(img, H, (S, S), flags=cv2.INTER_AREA)
        crop = cv2.resize(crop, (S*SCALE, S*SCALE), interpolation=cv2.INTER_CUBIC)
        rr, cc = k // COLS, k % COLS
        y0 = PAD + rr * (S*SCALE + PAD); x0 = PAD + cc * (S*SCALE + PAD)
        canvas[y0:y0+S*SCALE, x0:x0+S*SCALE] = crop
        cv2.putText(canvas, "#%d" % (i+1), (x0, y0-6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 220, 255), 1)
    out = os.path.join(BASE, "out", "labels", "hires_montage_%d.png" % (b+1))
    cv2.imencode(".png", canvas)[1].tofile(out)
    print("saved", out)
json.dump({"image": IMG, "quad": quad, "items": items},
          open(os.path.join(BASE, "out", "labels", "hires_candidates.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
