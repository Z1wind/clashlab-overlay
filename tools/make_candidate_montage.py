# -*- coding: utf-8 -*-
"""把位置候选裁成 96x96 拼成带索引的拼图（供人工/AI 标注类型/负样本）。"""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab import auto_candidates as ac
from clashlab.geo import Calib
import cv2, numpy as np
IMG = os.path.join(BASE, "out", "live", "enemy_scout_live.png")
QUAD = [[640,52],[1120,352],[640,652],[178,352]]
r = ac.candidates(IMG, QUAD, max_n=80, gate_only=True, gate_threshold=0.70, recall=True)
items = r.get("items") or []
print("items:", len(items))
img = cv2.imdecode(np.fromfile(IMG, np.uint8), cv2.IMREAD_COLOR)
cal = Calib.from_quad(np.asarray(QUAD, np.float32), n=44)
S = 96; SCALE = 2; PAD = 24; COLS = 6; ROWS = 4; PER = COLS * ROWS
os.makedirs(os.path.join(BASE, "out", "labels"), exist_ok=True)
meta = []
for idx, it in enumerate(items):
    x, y = it["tile"]; size = it["size"]
    p = [cal.tile_to_px(x,y), cal.tile_to_px(x+size,y), cal.tile_to_px(x+size,y+size), cal.tile_to_px(x,y+size)]
    H = cv2.getPerspectiveTransform(np.float32(p), np.float32([[0,0],[S,0],[S,S],[0,S]]))
    crop = cv2.warpPerspective(img, H, (S, S), flags=cv2.INTER_AREA)
    meta.append({"idx": idx+1, "tile": it["tile"], "size": size, "gate_conf": it.get("gate_conf")})
# 拼图（分批）
n_batches = (len(items) + PER - 1) // PER
for b in range(n_batches):
    canvas = np.full((ROWS * (S*SCALE + PAD) + PAD, COLS * (S*SCALE + PAD) + PAD, 3), 32, np.uint8)
    for k in range(PER):
        i = b * PER + k
        if i >= len(items):
            break
        it = items[i]
        x, y = it["tile"]; size = it["size"]
        p2 = [cal.tile_to_px(x,y), cal.tile_to_px(x+size,y), cal.tile_to_px(x+size,y+size), cal.tile_to_px(x,y+size)]
        H = cv2.getPerspectiveTransform(np.float32(p2), np.float32([[0,0],[S,0],[S,S],[0,S]]))
        crop = cv2.warpPerspective(img, H, (S, S), flags=cv2.INTER_AREA)
        crop = cv2.resize(crop, (S*SCALE, S*SCALE), interpolation=cv2.INTER_CUBIC)
        rr, cc = k // COLS, k % COLS
        y0 = PAD + rr * (S*SCALE + PAD); x0 = PAD + cc * (S*SCALE + PAD)
        canvas[y0:y0+S*SCALE, x0:x0+S*SCALE] = crop
        cv2.putText(canvas, "#%d" % (i+1), (x0, y0-6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 220, 255), 1)
    out = os.path.join(BASE, "out", "labels", "montage_%d.png" % (b+1))
    cv2.imencode(".png", canvas)[1].tofile(out)
    print("saved", out, canvas.shape)
json.dump(meta, open(os.path.join(BASE, "out", "labels", "candidates_meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("meta saved, batches:", n_batches)
