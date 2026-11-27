# -*- coding: utf-8 -*-
"""枚举 quad 角点顺序（24 种），用建筑处的颜色/纹理得分找正确映射。"""
import itertools, json, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
import cv2, numpy as np
from clashlab.geo import Calib
ann = json.load(open(BASE + "/out/annotate/01_annotated.json", encoding="utf-8"))
img = cv2.imdecode(np.fromfile(BASE + "/android/assets/img/b01.jpg", np.uint8), cv2.IMREAD_COLOR)
h, w = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
# 纹理图：局部方差
lap = cv2.Laplacian(gray, cv2.CV_32F)
var = cv2.blur(lap * lap, (15, 15))
sat = hsv[:, :, 1].astype(np.float32)
def score_for(quad):
    cal = Calib.from_quad(np.float32(quad), n=44)
    vals, satv, inside = [], [], 0
    for b in ann["buildings"]:
        x, y = b["tile"]; p = cal.tile_to_px(x + 0.5, y + 0.5)
        xi, yi = int(p[0]), int(p[1])
        if 0 <= xi < w and 0 <= yi < h:
            inside += 1
            vals.append(var[yi, xi]); satv.append(sat[yi, xi])
    if not vals: return -1e9, 0, 0
    return float(np.mean(vals) + 0.2 * np.mean(satv)), inside, len(vals)
m = re.search(r"quad=\[\[([^\]]+)\],\[([^\]]+)\],\[([^\]]+)\],\[([^\]]+)\]\]", ann["note"])
q0 = [[float(v) for v in g.split(",")] for g in m.groups()]
scale = w / 2622.0
q = [[x * scale, y * scale] for x, y in q0]
res = []
for perm in itertools.permutations(range(4)):
    quad = [q[i] for i in perm]
    sc, inside, n = score_for(quad)
    res.append((sc, perm, inside))
res.sort(reverse=True)
for sc, perm, inside in res[:6]:
    print(round(sc, 1), perm, "inside", inside, "/", len(ann["buildings"]))
print("worst:", round(res[-1][0], 1), res[-1][1])
