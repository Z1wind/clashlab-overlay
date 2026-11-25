# -*- coding: utf-8 -*-
import cv2, numpy as np, os
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
im = cv2.imdecode(np.fromfile(os.path.join(ROOT, "out", "overlay", "full", "raw", "probe_n.png"), dtype=np.uint8), cv2.IMREAD_COLOR)
# 对话框中部链接区放大
crop = im[380:470, 340:620]
crop = cv2.resize(crop, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
cv2.imencode(".png", crop)[1].tofile(os.path.join(ROOT, "out", "overlay", "full", "raw", "dlg_zoom.png"))
print("saved", im.shape)
