# -*- coding: utf-8 -*-
# b14_bluefind.py — 蓝青色(防空碟候选)像素簇检测，输出候选框供人工复核（新文件）
import os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EN = os.path.join(ROOT, "out", "overlay", "enemy")
SCRATCH = r"C:\Users\Admin（无密码）\AppData\Local\Doubao\User Data\Default\.doubao\agent_mode\workspace\.sessions\38455881728595202\agents\s_0007xvhw26c\scratch"
buf = np.fromfile(os.path.join(EN, "b14_ov1.png"), dtype=np.uint8)
im = cv2.imdecode(buf, cv2.IMREAD_COLOR)
# 裁口内基地范围（b14_full = ov1 195,88 - 1065,582）
roi = im[88:582, 195:1065].copy()
hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
# 青/蓝青色候选（防空碟主色）；排除绿草地
mask = cv2.inRange(hsv, np.array([75, 40, 50]), np.array([130, 255, 255]))
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
n, labels, stats, cent = cv2.connectedComponentsWithStats(mask)
boxes = []
for i in range(1, n):
    x, y, w, h, area = stats[i]
    if area >= 30:
        boxes.append((x + 195, y + 88, w, h, area, cent[i][0] + 195, cent[i][1] + 88))
boxes.sort(key=lambda b: -b[4])
vis = im.copy()
for k, (x, y, w, h, area, cx, cy) in enumerate(boxes[:25]):
    cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 0, 255), 2)
    cv2.putText(vis, f"#{k} a{area}", (x, y - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
    print(f"#{k} ov1=({x},{y}) {w}x{h} area={area} center=({cx:.0f},{cy:.0f})")
cv2.imencode(".png", vis)[1].tofile(os.path.join(SCRATCH, "b14_bluefind.png"))
print("total clusters", len(boxes))
