# -*- coding: utf-8 -*-
"""检查 8 张标注的四角是否风格统一（能否做「默认四角」按钮）。"""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np
DL = os.path.join(os.path.expanduser("~"), "Downloads")
paths = [os.path.join(DL, "annot_b01 (1).json"), os.path.join(DL, "annot_b02 (1).json")]
paths += [os.path.join(DL, "annot_b%02d.json" % i) for i in range(3, 9)]
allc = []
for p in paths:
    d = json.load(open(p, encoding="utf-8"))
    cn = np.array(d["corners_norm"], np.float32)
    allc.append(cn)
    print(os.path.basename(p), np.round(cn, 3).tolist())
arr = np.stack(allc)  # (8,4,2)
mean = arr.mean(0); std = arr.std(0)
print("\nMEAN", np.round(mean, 3).tolist())
print("STD ", np.round(std, 3).tolist(), "max_std", float(std.max()))
# 排序后的均值（消除点击顺序影响）：按 y 排序？这里直接看角点距离
print("\n每张与均值最大偏差(归一化):", float(np.abs(arr - mean).max()))
