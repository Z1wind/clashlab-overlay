# -*- coding: utf-8 -*-
# 离线：ref(zoom_L0) 中央模板 vs 当前帧多尺度匹配 → 尺度比 s → tile_px=24/s
import cv2, numpy as np, os
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ref = cv2.imdecode(np.fromfile(os.path.join(ROOT, "out", "overlay", "ladder", "zoom_L0.png"), dtype=np.uint8), cv2.IMREAD_COLOR)
cur = cv2.imdecode(np.fromfile(os.path.join(ROOT, "out", "overlay", "full", "raw", "wheel_test.png"), dtype=np.uint8), cv2.IMREAD_COLOR)
# 参考中央金仓/法师塔区域作模板
tpl = ref[250:420, 380:560]
gt = cv2.cvtColor(tpl, cv2.COLOR_BGR2GRAY)
best = None
for s in np.arange(0.55, 1.61, 0.05):
    resized = cv2.resize(gt, None, fx=s, fy=s)
    if resized.shape[0] > cur.shape[0] or resized.shape[1] > cur.shape[1]:
        continue
    cg = cv2.cvtColor(cur, cv2.COLOR_BGR2GRAY)
    r = cv2.matchTemplate(cg, resized, cv2.TM_CCOEFF_NORMED)
    _, mv, _, ml = cv2.minMaxLoc(r)
    if best is None or mv > best[0]:
        best = (mv, s, ml)
print("best corr=%.3f s=%.2f loc=%s" % (best[0], best[1], best[2]))
print("implied tile_px = 24/s =", round(24 / best[1], 2))
