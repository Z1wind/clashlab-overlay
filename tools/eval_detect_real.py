# -*- coding: utf-8 -*-
"""用训练好的检测器跑真实战图，输出可视化 + 命中统计。"""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ultralytics import YOLO
import cv2, numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
w = os.path.join(BASE, "out", "detect_runs", "v1", "weights", "best.pt")
img = os.path.join(BASE, "out", "live", "enemy_scout_live.png")
m = YOLO(w)
res = m.predict(img, conf=0.25, imgsz=640, device=0, verbose=False)[0]
names = res.names
counts = {}
for b in res.boxes:
    c = names[int(b.cls)]
    counts[c] = counts.get(c, 0) + 1
print("preds:", sum(counts.values()), "classes:", len(counts))
for k, v in sorted(counts.items(), key=lambda x: -x[1])[:15]:
    print("  ", k, v)
vis = res.plot()
out = os.path.join(BASE, "out", "live", "detect_eval.png")
cv2.imencode(".png", vis)[1].tofile(out)
print("saved", out)
