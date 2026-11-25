# -*- coding: utf-8 -*-
# v14_prep.py — b14 底图裁 UI 落盘，输出裁口。新文件。
import os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EN = os.path.join(ROOT, "out", "overlay", "enemy")
src = os.path.join(EN, "b14_ov1.png")
im = cv2.imdecode(np.fromfile(src, dtype=np.uint8), cv2.IMREAD_COLOR)
# 内容裁口：去左上奖励面板、底部进攻按钮/战争地图/回放、左右箭头
CROP = (195, 88, 1065, 662)
x1, y1, x2, y2 = CROP
crop = im[y1:y2, x1:x2]
cv2.imencode(".png", crop)[1].tofile(os.path.join(EN, "b14_full.png"))
print("b14_full", crop.shape[1], crop.shape[2] if crop.ndim == 3 else crop.shape[1], "crop", CROP)
# 存几份放大裁块供人工读数
regions = {
    "th":   (520, 250, 760, 470),   # 中心大本营 4x4
    "ne33": (700, 150, 950, 360),   # 右上 3x3 带
    "nw33": (300, 150, 560, 360),   # 左上
    "se33": (700, 430, 950, 640),   # 右下
    "sw33": (300, 430, 560, 640),   # 左下
}
for k, (a, b, c, d) in regions.items():
    r = im[b:d, a:c]
    r = cv2.resize(r, None, fx=2.2, fy=2.2, interpolation=cv2.INTER_CUBIC)
    cv2.imencode(".png", r)[1].tofile(os.path.join(EN, f"b14_{k}.png"))
print("done")
