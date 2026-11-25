# -*- coding: utf-8 -*-
import os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EN = os.path.join(ROOT, "out", "overlay", "enemy")
im = cv2.imdecode(np.fromfile(os.path.join(EN, "b14_pan_d2.png"), dtype=np.uint8), cv2.IMREAD_COLOR)
x1, y1, x2, y2 = (560, 490, 730, 610)
c = im[y1:y2, x1:x2].copy()
for x in range(0, c.shape[1], 10):
    cv2.line(c, (x, 0), (x, c.shape[0]), (0, 255, 255), 1)
    cv2.putText(c, str(x1+x), (x+1, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0,255,255), 1)
for y in range(0, c.shape[0], 10):
    cv2.line(c, (0, y), (c.shape[1], y), (0, 255, 255), 1)
    cv2.putText(c, str(y1+y), (1, y+10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0,255,255), 1)
c = cv2.resize(c, None, fx=3.5, fy=3.5, interpolation=cv2.INTER_NEAREST)
cv2.imencode(".png", c)[1].tofile(os.path.join(EN, "b14_cB2.png"))
# 配准：用 ov1 与 pan_d2 中心墙块互相关求平移
a = cv2.imdecode(np.fromfile(os.path.join(EN,"b14_ov1.png"),dtype=np.uint8),cv2.IMREAD_GRAYSCALE)
b = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
# 取 pan 帧中央区域在 ov1 中匹配
patch = b[200:500, 450:830]
res = cv2.matchTemplate(a, patch, cv2.TM_CCOEFF_NORMED)
_, mx, _, ml = cv2.minMaxLoc(res)
print("match top-left ov1:", ml, "offset:", (ml[0]-450, ml[1]-200))
