# -*- coding: utf-8 -*-
"""把已采标签点转成裁剪样本：一次干净截图 → 每点裁 108×108 → 存 sweep3/。"""
import json, os
import numpy as np, cv2
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
AUTO = os.path.join(BASE, "out", "overlay", "_auto_label")

labels = json.load(open(os.path.join(AUTO, "g3_labels.json"), encoding="utf-8"))
img = cv2.imdecode(np.fromfile(os.path.join(AUTO, "after_close.png"), np.uint8), cv2.IMREAD_COLOR)
os.makedirs(os.path.join(AUTO, "sweep3"), exist_ok=True)
keep, seen = [], []
for r in labels:
    if not r.get("name") or r.get("ratio", 0) < 0.55:
        continue
    if any((r["x"] - s[0]) ** 2 + (r["y"] - s[1]) ** 2 < 40 ** 2 for s in seen):
        continue
    x, y = r["x"], r["y"]
    c = img[y - 54:y + 54, x - 54:x + 54]
    if c.shape[0] != 108 or c.shape[1] != 108:
        continue
    p = os.path.join(AUTO, "sweep3", "g3_%d_%d.png" % (x, y))
    cv2.imencode(".png", c)[1].tofile(p)
    seen.append((x, y))
    keep.append({"x": x, "y": y, "name": r["name"], "type": r["type"], "ratio": r["ratio"]})
json.dump(keep, open(os.path.join(AUTO, "g3_labels_clean.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
from collections import Counter
print("kept=%d" % len(keep))
print("classes=", dict(Counter(k["type"] for k in keep)))
print("names=", dict(Counter(k["name"] for k in keep)))
