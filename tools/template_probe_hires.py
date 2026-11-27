# -*- coding: utf-8 -*-
"""高分辨率截图上的建筑立绘模板匹配试验（多尺度 + 掩膜）。"""
import glob, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
IMG = os.path.join(BASE, "out", "live", "hires", "coc_193842_6.png")
img = cv2.imdecode(np.fromfile(IMG, np.uint8), cv2.IMREAD_COLOR)
print("img", img.shape)
BUILD = os.path.join(BASE, "assets", "clashking", "buildings")
def load_template(name, level=16):
    cands = sorted(glob.glob(os.path.join(BUILD, name, "level_*.webp")))
    if not cands:
        return None
    p = [c for c in cands if c.endswith("level_%d.webp" % level)] or [cands[-1]]
    t = cv2.imdecode(np.fromfile(p[0], np.uint8), cv2.IMREAD_UNCHANGED)
    return t
for name, level in (("inferno_tower", 9), ("eagle_artillery", 1), ("scattershot", 1), ("monolith", 1)):
    t = load_template(name, level)
    if t is None:
        print(name, "no template"); continue
    print(name, "template", t.shape)
    if t.ndim == 3 and t.shape[2] == 4:
        alpha = t[:, :, 3]
        bgr = t[:, :, :3]
    else:
        alpha = np.full(t.shape[:2], 255, np.uint8); bgr = t
    best = None
    for scale in (0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2):
        tw = int(bgr.shape[1] * scale); th = int(bgr.shape[0] * scale)
        if tw < 12 or th < 12 or tw > img.shape[1] or th > img.shape[0]:
            continue
        tpl = cv2.resize(bgr, (tw, th), interpolation=cv2.INTER_AREA)
        msk = cv2.resize(alpha, (tw, th), interpolation=cv2.INTER_NEAREST)
        res = cv2.matchTemplate(img, tpl, cv2.TM_CCORR_NORMED, mask=msk)
        res = np.nan_to_num(res, nan=0.0, posinf=0.0, neginf=0.0)
        _, mx, _, loc = cv2.minMaxLoc(res)
        if best is None or mx > best[0]:
            best = (mx, loc, (tw, th), scale)
    print("  best:", round(best[0], 3), "loc:", best[1], "size:", best[2], "scale:", best[3])
