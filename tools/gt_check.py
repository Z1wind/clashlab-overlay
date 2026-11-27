# -*- coding: utf-8 -*-
"""把 01_annotated 的 GT 建筑画到 b01 上，检查 quad 对齐。"""
import json, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
import cv2, numpy as np
from clashlab.geo import Calib
ann = json.load(open(BASE + r"\out\annotate\01_annotated.json", encoding="utf-8"))
img = cv2.imdecode(np.fromfile(BASE + r"\android\assets\img\b01.jpg", np.uint8), cv2.IMREAD_COLOR)
note = ann.get("note") or ""
m = re.search(r"quad=\[\[([^\]]+)\],\[([^\]]+)\],\[([^\]]+)\],\[([^\]]+)\]\]", note)
q = np.array([[float(v) for v in g.split(",")] for g in m.groups()], np.float32)
quad = q * (img.shape[1] / 2622.0)
cal = Calib.from_quad(quad, n=44)
vis = img.copy()
for b in ann["buildings"]:
    x, y = b["tile"]; p = cal.tile_to_px(x + 0.5, y + 0.5)
    cv2.circle(vis, (int(p[0]), int(p[1])), 6, (0, 0, 255), 2)
cv2.imencode(".png", vis)[1].tofile(BASE + r"\out\layouts_src\gt_check_b01.png")
print("saved gt_check_b01.png | buildings:", len(ann["buildings"]))
# 同时画网格四角
for i, p in enumerate(quad):
    cv2.circle(vis, (int(p[0]), int(p[1])), 9, (255, 0, 255), 3)
cv2.imencode(".png", vis)[1].tofile(BASE + r"\out\layouts_src\gt_check_corners.png")
