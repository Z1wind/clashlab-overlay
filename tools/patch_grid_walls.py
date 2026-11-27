# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "grid_from_walls.py")
t = open(p, encoding="utf-8").read()
old = '''n, lab, stats, cents = cv2.connectedComponentsWithStats(mask, 8)
best = None
for i in range(1, n):
    if stats[i, 4] < 400:
        continue
    m = (lab == i).astype(np.uint8)
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    c = max(cnts, key=cv2.contourArea)
    area = cv2.contourArea(c)
    if area < 2000:
        continue
    rect = cv2.minAreaRect(c)
    w2, h2 = rect[1]
    ar = max(w2, h2) / max(1.0, min(w2, h2))
    if ar > 1.8:
        continue
    if best is None or area > best[0]:
        best = (area, rect, c)
print("wall components:", n, "best area:", None if best is None else best[0])
if best is None:
    raise SystemExit("no wall component")
rect = best[1]
box = cv2.boxPoints(rect).astype(np.float32)'''
new = '''# 全部蓝墙像素合并求最小外接旋转矩形（整圈墙）
ys, xs = np.where(mask > 0)
keep = (xs > img.shape[1] * 0.04) & (xs < img.shape[1] * 0.96) & (ys > img.shape[0] * 0.04) & (ys < img.shape[0] * 0.96)
pts = np.stack([xs[keep], ys[keep]], axis=1).astype(np.float32)
print("wall pixels:", len(pts))
if len(pts) < 500:
    raise SystemExit("too few wall pixels")
rect = cv2.minAreaRect(pts)
box = cv2.boxPoints(rect).astype(np.float32)'''
if old in t:
    t = t.replace(old, new, 1)
    t = t.replace('print("wall components:", n, "best area:", None if best is None else best[0])', '')
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("patched")
else:
    print("anchor miss")
