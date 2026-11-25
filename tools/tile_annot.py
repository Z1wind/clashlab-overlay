# -*- coding: utf-8 -*-
# v6_zoom_max_tile.png：标注实测墙段中心距(35/46/35px) + 35px标尺
import cv2, numpy as np, os
OUT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay"
img = cv2.imdecode(np.fromfile(os.path.join(OUT,"v6_zoom_max_raw.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
vis=img.copy()
# 旧检测线上的4个帽中心(实测峰位 s=40,75,121,156; P0(335,5) u=(0.724,0.690))
P0=np.array([335.0,5.0]); u=np.array([0.724,0.690])
peaks=[40,75,121,156]
pts=[P0+u*s for s in peaks]
for i,p in enumerate(pts):
    cv2.circle(vis,tuple(p.astype(int)),9,(0,0,255),2)
for a,bv in zip(pts[:-1],pts[1:]):
    cv2.line(vis,tuple(a.astype(int)),tuple(bv.astype(int)),(0,0,255),1)
    m=(a+bv)/2
    cv2.putText(vis,"%.0fpx"%(np.linalg.norm(bv-a)),tuple(m.astype(int)+[0,-8]),
                cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,0,255),2)
# 35px 标尺（左下角空地不可达，放左上标题区旁）
cv2.line(vis,(40,60),(75,60),(0,255,0),3)
cv2.putText(vis,"tile_px ~35px (wall cap step, median)",(40,52),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,255,0),2)
cv2.imencode(".png",vis)[1].tofile(os.path.join(OUT,"v6_zoom_max_tile.png"))
print("saved")
