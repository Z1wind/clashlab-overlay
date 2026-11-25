# -*- coding: utf-8 -*-
"""base_map.py — 拼接底图内容密度 ASCII 图（纯离线）。"""
import sys
import cv2
import numpy as np

img = cv2.imdecode(np.fromfile(sys.argv[1], dtype=np.uint8), cv2.IMREAD_COLOR)
h, w = img.shape[:2]
# 非黑掩膜
non = (img.max(axis=2) > 25).astype(np.uint8)
# 缩到 96x40 网格
gh, gw = 40, 96
small = cv2.resize(non, (gw, gh), interpolation=cv2.INTER_AREA)
chars = " .:-=+*#%@"
for r in range(gh):
    row = "".join(chars[min(9, int(small[r, c] * 10))] for c in range(gw))
    print(row)
print(f"canvas {w}x{h}; 列刻度 0..{gw} 对应 x 0..{w}")
