# -*- coding: utf-8 -*-
"""生成 cannon 裁剪 vs 各等级 sprite 的对照图，检查配色匹配是否可行。"""
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
# 找所有 cannon
tiles = [b["tile"] for b in ann["buildings"] if b["type"] == "cannon"][:4]
print("cannon tiles:", tiles)
tiles = tiles or [[26, 10]]
crops = [level_visual.crop_building(img, calib, t, 3) for t in tiles]
# 取第一张与等级 sprite 拼图
tpl_dir = os.path.join(BASE, "assets", "coc", "buildings", "cannon")
levels = [1, 5, 10, 15, 18, 21]
cells = []
first = crops[0]
cells.append(("crop", first))
for lv in levels:
    p = os.path.join(tpl_dir, "level-%d.png" % lv)
    s = cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_UNCHANGED)
    if s is None:
        continue
    if s.shape[2] == 4:
        a = s[:, :, 3:4].astype(np.float32) / 255.0
        rgb = (s[:, :, :3].astype(np.float32) * a + 40 * (1 - a)).astype(np.uint8)
    else:
        rgb = s
    cells.append(("L%d" % lv, cv2.resize(rgb, (level_visual.CROP, level_visual.CROP))))
W = level_visual.CROP
canvas = np.full((W + 26, len(cells) * (W + 8), 3), 30, np.uint8)
for i, (label, im) in enumerate(cells):
    x = i * (W + 8) + 4
    canvas[22:22 + W, x:x + W] = im
    cv2.putText(canvas, label, (x, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (240, 240, 240), 1)
out = os.path.join(BASE, "out", "annotate", "cannon_level_montage.png")
cv2.imencode(".png", canvas)[1].tofile(out)
print("montage:", out)
# 也输出所有 cannon 的 crop 拼图
strip = np.full((W + 8, len(crops) * (W + 8), 3), 30, np.uint8)
for i, im in enumerate(crops):
    x = i * (W + 8) + 4
    strip[4:4 + W, x:x + W] = im
cv2.imencode(".png", strip)[1].tofile(os.path.join(BASE, "out", "annotate", "cannon_crops.png"))
print("crops saved")
