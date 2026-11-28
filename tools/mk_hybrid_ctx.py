# -*- coding: utf-8 -*-
"""实验：门控上下文 6x6 格（vs 4x4），其余同混合方案。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = os.path.join(BASE, "tools", "train_hybrid_cv.py")
t = open(src, encoding="utf-8").read()
# 新增 6x6 warp
t = t.replace("def warp_gray(img, cal, cx, cy, size):" if "def warp_gray" in t else "def warp(img, cal, cx, cy, size):",
"""def warp6(img, cal, cx, cy, size):
    x0, y0 = cx - 2.5, cy - 2.5
    p = [cal.tile_to_px(x0,y0), cal.tile_to_px(x0+6,y0), cal.tile_to_px(x0+6,y0+6), cal.tile_to_px(x0,y0+6)]
    H = cv2.getPerspectiveTransform(np.float32(p), np.float32([[0,0],[size,0],[size,size],[0,size]]))
    return cv2.warpPerspective(img, H, (size,size), flags=cv2.INTER_AREA)
def warp(img, cal, cx, cy, size):""", 1)
# 门控训练与评估用 warp6；embedding 保持 warp
t = t.replace("gpos.append((crop(", "gpos.append((crop(")  # noop
t = t.replace('gpos.append((warp(img, cal, gx, gy), 1))', 'gpos.append((warp6(img, cal, gx, gy), 1))')
t = t.replace('gneg.append((warp(img, cal, cx, cy), 0))', 'gneg.append((warp6(img, cal, cx, cy), 0))')
t = t.replace('gpos.append((crop(img, cal, gx, gy), 1))', 'gpos.append((crop6(img, cal, gx, gy), 1))')
t = t.replace('gneg.append((crop(img, cal, cx, cy), 0))', 'gneg.append((crop6(img, cal, cx, cy), 0))')
# 评估时 gate 用 warp6：找到评估循环中 gate 的输入
t = t.replace('xs = np.stack([warp(img, cal, cx, cy) for (cx,cy) in cs])', 'xs = np.stack([warp6(img, cal, cx, cy) for (cx,cy) in cs])')
t = t.replace('xs = np.stack([crop(img, cal, cx, cy) for (cx,cy) in cs])', 'xs = np.stack([warp6(img, cal, cx, cy) for (cx,cy) in cs])')
t = t.replace('hybrid_report.json', 'hybrid_ctx_report.json')
open(os.path.join(BASE, "tools", "train_hybrid_ctx_cv.py"), "w", encoding="utf-8", newline="\n").write(t)
print("ctx script written; warp6 count:", t.count("warp6"))
