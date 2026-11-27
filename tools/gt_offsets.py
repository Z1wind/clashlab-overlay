# -*- coding: utf-8 -*-
"""检查 GT 偏移：用原始 quad，按不同中心偏移画点。"""
import json, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
import cv2, numpy as np
from clashlab.geo import Calib
ann = json.load(open(BASE + "/out/annotate/01_annotated.json", encoding="utf-8"))
img = cv2.imdecode(np.fromfile(BASE + "/android/assets/img/b01.jpg", np.uint8), cv2.IMREAD_COLOR)
m = re.search(r"quad=\[\[([^\]]+)\],\[([^\]]+)\],\[([^\]]+)\],\[([^\]]+)\]\]", ann["note"])
q = np.array([[float(v) for v in g.split(",")] for g in m.groups()], np.float32) * (img.shape[1] / 2622.0)
cal = Calib.from_quad(q, n=44)
for off, tag in (((0.5, 0.5), "c05"), ((1.0, 1.0), "c10"), ((0.75, 0.75), "c075")):
    vis = img.copy()
    for b in ann["buildings"]:
        x, y = b["tile"]
        p = cal.tile_to_px(x + off[0], y + off[1])
        cv2.circle(vis, (int(p[0]), int(p[1])), 5, (0, 0, 255), 2)
    cv2.imencode(".png", vis)[1].tofile(BASE + "/out/layouts_src/off_" + tag + ".png")
    print("saved off_" + tag)
