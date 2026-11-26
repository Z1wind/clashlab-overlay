# -*- coding: utf-8 -*-
"""带 alpha mask 的多尺度模板匹配：给真实战图提候选建筑（仅用于近似标注）。"""
import glob, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
shot = cv2.imdecode(np.fromfile(os.path.join(BASE, "out", "live", "enemy_scout_live.png"), np.uint8), cv2.IMREAD_COLOR)
H, W = shot.shape[:2]
SPR = os.path.join(BASE, "assets", "clashking", "buildings")
TYPES = ["air-defense", "air-sweeper", "monolith", "eagle_artillery", "scattershot", "town_hall", "x_bow", "inferno_tower"]
CANDS = []
for typ in TYPES:
    d = os.path.join(SPR, typ)
    files = sorted(glob.glob(os.path.join(d, "level_*.webp")))
    if not files:
        continue
    for f in files[-3:]:
        spr = cv2.imdecode(np.fromfile(f, np.uint8), cv2.IMREAD_UNCHANGED)
        if spr is None or spr.shape[2] != 4:
            continue
        bgr = spr[:, :, :3]
        mask = (spr[:, :, 3] > 40).astype(np.uint8) * 255
        for sc in (0.14, 0.16, 0.18, 0.20, 0.22):
            h = int(bgr.shape[0] * sc); w = int(bgr.shape[1] * sc)
            if h < 20 or w < 20 or h >= H or w >= W:
                continue
            t = cv2.resize(bgr, (w, h)); m = cv2.resize(mask, (w, h))
            if m.sum() < 50 * 255:
                continue
            try:
                res = cv2.matchTemplate(shot, t, cv2.TM_CCORR_NORMED, mask=m)
            except Exception:
                continue
            res = np.nan_to_num(res)
            for _ in range(2):
                _, mx, _, loc = cv2.minMaxLoc(res)
                if mx < 0.55:
                    break
                cx, cy = loc[0] + w // 2, loc[1] + h // 2
                CANDS.append((float(mx), typ, cx, cy, w, h))
                cv2.rectangle(res, (loc[0] - w, loc[1] - h), (loc[0] + w, loc[1] + h), 0, -1)
CANDS.sort(reverse=True)
picked = []
for c in CANDS:
    if all(abs(c[2] - p[2]) > 40 or abs(c[3] - p[3]) > 40 for p in picked):
        picked.append(c)
picked = picked[:16]
print("top candidates:", [(round(c[0], 2), c[1], c[2], c[3]) for c in picked[:12]])
vis = shot.copy()
for score, typ, cx, cy, w, h in picked:
    cv2.rectangle(vis, (cx - w // 2, cy - h // 2), (cx + w // 2, cy + h // 2), (0, 0, 255), 2)
    cv2.putText(vis, typ[:10], (cx - 20, cy - h // 2 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
out = os.path.join(BASE, "out", "live", "tmpl_candidates.png")
cv2.imencode(".png", vis)[1].tofile(out)
print("saved", out)
