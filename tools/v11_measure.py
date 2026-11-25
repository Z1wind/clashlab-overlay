# -*- coding: utf-8 -*-
# v11_measure.py — 对最远 home 帧量 tile_px（三判据），输出到控制台。新文件。
import sys, os, cv2, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v6_tile_px import measure_tile_px

ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "out", "overlay", "full", "raw", "pinchin_far.png")
im = cv2.imdecode(np.fromfile(src, dtype=np.uint8), cv2.IMREAD_COLOR)
print("FULL ", measure_tile_px(im))
# 内容裁口（去顶奖励条/右资源轨/底按钮/左工具栏）
TRIM = (150, 75, 1015, 612)
x1, y1, x2, y2 = TRIM
crop = im[y1:y2, x1:x2]
print("TRIM ", measure_tile_px(crop))
