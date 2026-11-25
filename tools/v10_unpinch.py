# -*- coding: utf-8 -*-
# v10_unpinch.py — 连续 pinch-in 到 MAD plateau（回 L0 全村远景），逐帧存 raw/unpinch_N.png
import sys, os, time, cv2, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v10_lib import grab, sh, mad, RAW

prev = grab()
plateau = 0
for i in range(25):
    sh(["shell", "sh", "/data/local/tmp/pinchin.sh", "14", "10"])
    time.sleep(1.8)
    cur = grab()
    m = mad(prev, cur)
    cv2.imencode(".png", cur)[1].tofile(os.path.join(RAW, f"unpinch_{i:02d}.png"))
    print(f"b{i:02d} MAD={m:.2f}")
    if m < 1.5:
        plateau += 1
        if plateau >= 3:
            print("PLATEAU"); break
    else:
        plateau = 0
    prev = cur
print("done")
