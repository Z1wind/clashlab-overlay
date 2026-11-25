# -*- coding: utf-8 -*-
# v12_measure.py — 侦察帧 tool3 三判据记录。新文件。
import sys, os, cv2, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v6_tile_px import measure_tile_px
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "out", "overlay", "full", "raw", "v12_n4.png")
im = cv2.imdecode(np.fromfile(src, dtype=np.uint8), cv2.IMREAD_COLOR)
print(measure_tile_px(im))
