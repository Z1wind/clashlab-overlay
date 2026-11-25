# -*- coding: utf-8 -*-
# v10_sweep.py — 长时长 input swipe 平移，ORB 累计 vs ref，到目标/停滞后停。
# 用法: v10_sweep.py DIR TARGET_PX [ref] [--once]
import sys, os, time, cv2, numpy as np, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v10_lib import grab, trim, orb_shift, FULL

ADB = r"E:\leidian\LDPlayer9\adb.exe"
SWIPE = {
    "N": "500 560 500 200 900",
    "S": "500 200 500 560 900",
    "E": "700 300 300 300 900",
    "W": "300 300 700 300 900",
}

def main():
    d, target = sys.argv[1], float(sys.argv[2])
    refname = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else "b00.png"
    ref = cv2.imdecode(np.fromfile(os.path.join(FULL, refname), dtype=np.uint8), cv2.IMREAD_COLOR)
    ref = trim(ref)
    stall = 0
    for i in range(14):
        subprocess.run([ADB, "shell", "input", "swipe", *SWIPE[d].split()], capture_output=True, timeout=30)
        time.sleep(1.8)
        cur = trim(grab())
        shift, nin, ng = orb_shift(ref, cur)
        if shift is None:
            print(f"i{i}: no match {nin}/{ng}")
            continue
        sx, sy = shift
        print(f"i{i}: cum=({sx:.1f},{sy:.1f}) inl={nin}/{ng}")
        val = sx if d in ("E", "W") else sy
        if abs(val) >= abs(target):
            print("REACHED"); return
        stall = stall + 1 if abs(val) < 3 else 0
        if stall >= 2:
            print("STALLED (boundary)"); return
    print("done")

if __name__ == "__main__":
    main()
