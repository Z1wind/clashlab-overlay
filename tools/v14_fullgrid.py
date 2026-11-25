# -*- coding: utf-8 -*-
# v14_fullgrid.py — ov1 全帧 20px 网格标注，供读四角与外墙 bay 计数。新文件。
import os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EN = os.path.join(ROOT, "out", "overlay", "enemy")
im = cv2.imdecode(np.fromfile(os.path.join(EN, "b14_ov1.png"), dtype=np.uint8), cv2.IMREAD_COLOR)
c = im.copy()
for x in range(0, 1280, 20):
    cv2.line(c, (x, 0), (x, 720), (0, 255, 255), 1)
    if x % 40 == 0:
        cv2.putText(c, str(x), (x + 2, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
for y in range(0, 720, 20):
    cv2.line(c, (0, y), (1280, y), (0, 255, 255), 1)
    if y % 40 == 0:
        cv2.putText(c, str(y), (2, y + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
cv2.imencode(".png", c)[1].tofile(os.path.join(EN, "b14_fullgrid.png"))
print("ok")
