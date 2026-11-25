# -*- coding: utf-8 -*-
# v14_grid.py — 在 ov1 指定区域画 20px 坐标线并标注，供人工读数。新文件。
import os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EN = os.path.join(ROOT, "out", "overlay", "enemy")
im = cv2.imdecode(np.fromfile(os.path.join(EN, "b14_ov1.png"), dtype=np.uint8), cv2.IMREAD_COLOR)

def annot(box, name, step=20, scale=2.0):
    x1, y1, x2, y2 = box
    c = im[y1:y2, x1:x2].copy()
    for x in range(0, c.shape[1], step):
        cv2.line(c, (x, 0), (x, c.shape[0]), (0, 255, 255), 1)
        cv2.putText(c, str(x1 + x), (x + 2, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)
    for y in range(0, c.shape[0], step):
        cv2.line(c, (0, y), (c.shape[1], y), (0, 255, 255), 1)
        cv2.putText(c, str(y1 + y), (2, y + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)
    c = cv2.resize(c, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
    cv2.imencode(".png", c)[1].tofile(os.path.join(EN, name))
    print(name, box)

# 中心 TH 区
annot((540, 270, 760, 460), "b14_g_th.png", 20, 2.2)
# 右上 3x3 区
annot((720, 150, 960, 380), "b14_g_ne.png", 20, 2.0)
# 左上
annot((280, 150, 520, 380), "b14_g_nw.png", 20, 2.0)
# 右下
annot((720, 420, 960, 650), "b14_g_se.png", 20, 2.0)
# 左下
annot((280, 420, 520, 650), "b14_g_sw.png", 20, 2.0)
