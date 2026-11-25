# -*- coding: utf-8 -*-
# 裁剪条带放大供人工读边：参数 top|bottom|left|right
import cv2, numpy as np, os, sys
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
im = cv2.imdecode(np.fromfile(os.path.join(ROOT, "out", "overlay", "full", "b00.png"), dtype=np.uint8), cv2.IMREAD_COLOR)
region = sys.argv[1] if len(sys.argv) > 1 else "top"
h, w = im.shape[:2]
if region == "top":
    c = im[0:180, :]
elif region == "bottom":
    c = im[h-180:h, :]
elif region == "left":
    c = im[:, 0:200]
else:
    c = im[:, w-200:w]
c = cv2.resize(c, None, fx=2.2, fy=2.2, interpolation=cv2.INTER_CUBIC)
out = os.path.join(ROOT, "out", "overlay", "full", "raw", f"strip_{region}.png")
cv2.imencode(".png", c)[1].tofile(out)
print("saved", out, im.shape)
