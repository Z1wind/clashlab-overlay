# -*- coding: utf-8 -*-
"""在已下载的 20 张站图上试 detect_village_quad，估算自动标注成功率。"""
import glob, os, sys
import cv2
sys.path.insert(0, r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat")
from clashlab import calib as calib_mod
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
files = sorted(glob.glob(os.path.join(BASE, "out", "sceneries", "*.jpg")))
print("images:", len(files))
ok = 0
for f in files:
    img = cv2.imdecode(__import__("numpy").fromfile(f, __import__("numpy").uint8), cv2.IMREAD_COLOR)
    if img is None:
        print(os.path.basename(f), "read fail"); continue
    try:
        calib, meta = calib_mod.detect_village_quad(img, grid_n=44)
    except Exception as e:
        print(os.path.basename(f), "ERR", str(e)[:60]); continue
    quad = meta.get("quad")
    area = 0.0
    if quad:
        q = __import__("numpy").array(quad, float)
        s = 0.0
        for i in range(4):
            s += q[i][0] * q[(i + 1) % 4][1] - q[(i + 1) % 4][0] * q[i][1]
        area = abs(s) / 2.0 / float(img.shape[0] * img.shape[1])
    good = calib is not None and 0.15 <= area <= 0.95
    ok += good
    print("%-28s method=%-12s area=%.3f good=%s" % (os.path.basename(f), meta.get("method"), area, good))
print("success:", ok, "/", len(files))
