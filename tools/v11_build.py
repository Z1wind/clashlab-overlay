# -*- coding: utf-8 -*-
# v11_build.py — fallback：编辑器入口未找到，把 L0 最远 home 帧裁 UI 存为 v11_editor_full.png。新文件。
import os, cv2, numpy as np, json, datetime
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
FULL = os.path.join(ROOT, "out", "overlay", "full")
src = os.path.join(FULL, "raw", "pinchin_far.png")
im = cv2.imdecode(np.fromfile(src, dtype=np.uint8), cv2.IMREAD_COLOR)
TRIM = (150, 75, 1015, 612)
x1, y1, x2, y2 = TRIM
crop = im[y1:y2, x1:x2]
cv2.imencode(".png", crop)[1].tofile(os.path.join(FULL, "v11_editor_full.png"))
h, w = crop.shape[:2]
print("saved v11_editor_full.png", w, h)
