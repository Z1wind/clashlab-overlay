# -*- coding: utf-8 -*-
"""实验：ClashKing 立绘多尺度模板匹配真实战图（只测几个大件）。"""
import glob, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
IMG = os.path.join(BASE, "out", "live", "enemy_scout_live.png")
shot = cv2.imdecode(np.fromfile(IMG, np.uint8), cv2.IMREAD_COLOR)
H, W = shot.shape[:2]
print("shot", shot.shape)
SPR = os.path.join(BASE, "assets", "clashking", "buildings")
for typ in ("town_hall", "monolith", "eagle_artillery", "scattershot", "air_defense", "air_sweeper", "inferno_tower", "x_bow"):
    d = os.path.join(SPR, typ)
    files = sorted(glob.glob(os.path.join(d, "level_*.webp")))
    if not files:
        print(typ, "no sprites"); continue
    best = []
    for f in files[-6:]:  # 高等级几张
        spr = cv2.imdecode(np.fromfile(f, np.uint8), cv2.IMREAD_COLOR)
        if spr is None: continue
        for sc in (0.10, 0.13, 0.16, 0.20, 0.25, 0.30, 0.36):
            h = int(spr.shape[0] * sc); w = int(spr.shape[1] * sc)
            if h < 24 or w < 24 or h >= H or w >= W: continue
            t = cv2.resize(spr, (w, h), interpolation=cv2.INTER_AREA)
            res = cv2.matchTemplate(shot, t, cv2.TM_CCOEFF_NORMED)
            _, mx, _, loc = cv2.minMaxLoc(res)
            if mx > 0.45:
                best.append((round(float(mx), 3), os.path.basename(f), sc, loc))
    best.sort(reverse=True)
    print(typ, "top:", best[:3], "count>0.45:", len(best))
