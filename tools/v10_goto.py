# -*- coding: utf-8 -*-
# v10_goto.py — 相对 b00 循环小步拖动，直到 ORB 累计位移达到目标（裁口 px）。
# 用法: v10_goto.py E|W|N|S TARGET_PX [ref]
import sys, os, time, cv2, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v10_lib import grab, trim, orb_shift, sh, FULL

STEP = 130
DRAG = {
    "N": (640, 300, 640, 300 - STEP),
    "S": (640, 300, 640, 300 + STEP),
    "E": (640, 300, 640 - STEP, 300),
    "W": (640, 300, 640 + STEP, 300),
}

def main():
    d, target = sys.argv[1], float(sys.argv[2])
    refname = sys.argv[3] if len(sys.argv) > 3 else "b00.png"
    ref = cv2.imdecode(np.fromfile(os.path.join(FULL, refname), dtype=np.uint8), cv2.IMREAD_COLOR)
    ref = trim(ref)
    for i in range(12):
        x0, y0, x1, y1 = DRAG[d]
        sh(["shell", "sh", "/data/local/tmp/drag.sh", str(x0), str(y0), str(x1), str(y1), "12"])
        time.sleep(1.4)
        cur = trim(grab())
        shift, nin, ng = orb_shift(ref, cur)
        if shift is None:
            print(f"goto {d} i{i}: no match {nin}/{ng}")
            continue
        sx, sy = shift
        print(f"goto {d} i{i}: cum=({sx:.1f},{sy:.1f}) inl={nin}/{ng}")
        val = sx if d in ("E", "W") else sy
        if abs(val) >= abs(target):
            print("REACHED")
            return
    print("goto done (not reached)")

if __name__ == "__main__":
    main()
