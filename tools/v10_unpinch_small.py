# -*- coding: utf-8 -*-
# 小展开 pinch-in 循环：逐批存 raw/in_NN.png，报 MAD；人工看是否逐步缩远。
import sys, os, time, cv2, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v10_lib import grab, sh, mad, RAW
prev = grab()
for i in range(12):
    sh(["shell", "sh", "/data/local/tmp/pinch_small.sh"])
    time.sleep(1.6)
    cur = grab()
    m = mad(prev, cur)
    cv2.imencode(".png", cur)[1].tofile(os.path.join(RAW, f"in_{i:02d}.png"))
    print(f"b{i:02d} MAD={m:.2f}")
    prev = cur
print("done")
