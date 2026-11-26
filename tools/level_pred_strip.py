# -*- coding: utf-8 -*-
"""按类型输出预测等级 + 裁剪图，拼一张人工核对图。"""
import json, os, sys
import numpy as np, cv2
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab import level_visual, geo

def load(p): return json.load(open(p, encoding="utf-8"))
img = cv2.imdecode(np.fromfile(os.path.join(BASE, "bases", "th16", "03", "base.png"), np.uint8), cv2.IMREAD_COLOR)
ann = load(os.path.join(BASE, "out", "annotate", "03_annotated.json"))
quad = load(os.path.join(BASE, "out", "annotate", "03_quad.json"))["quad"]
calib = geo.Calib.from_quad(quad, n=44)
est = { (x["type"], tuple(x["tile"])): x for x in load(os.path.join(BASE, "out", "annotate", "level_estimates.json"))["results"][0]["buildings"] }
want = ["cannon", "archer-tower", "x-bow", "inferno-tower", "air-defense", "scattershot"]
rows = []
for b in ann["buildings"]:
    if b["type"] in want:
        rows.append(b)
rows = rows[:12]
W = level_visual.CROP
canvas = np.full((W + 30, len(rows) * (W + 8), 3), 26, np.uint8)
for i, b in enumerate(rows):
    t = b["type"]; size = 4 if t == "town-hall" else (2 if t in ("inferno-tower", "hidden-tesla", "air-sweeper", "spell-tower") else 3)
    crop = level_visual.crop_building(img, calib, b["tile"], size)
    e = est.get((t, tuple(b["tile"]))) or {}
    x = i * (W + 6) + 3
    canvas[26:26 + W, x:x + W] = crop
    cv2.putText(canvas, "%s" % t[:9], (x, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (230, 230, 230), 1)
    cv2.putText(canvas, "L%s c%.2f" % (e.get("level_est"), e.get("confidence") or 0), (x, 26 + W + 14),
                cv2.FONT_HERSHEY_SIMPLEX, 0.33, (120, 220, 160), 1)
out = os.path.join(BASE, "out", "annotate", "level_pred_strip.png")
cv2.imencode(".png", canvas)[1].tofile(out)
print("saved", out)
for b in rows:
    e = est.get((b["type"], tuple(b["tile"]))) or {}
    print(b["type"], b["tile"], "->", e.get("level_est"), "conf", e.get("confidence"))
