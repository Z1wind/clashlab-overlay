# -*- coding: utf-8 -*-
# 白帽(墙段顶)亮斑检测：低饱和高亮方块，ROI内连通域中心
import cv2, numpy as np, os, math
D=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\ladder"
img=cv2.imdecode(np.fromfile(os.path.join(D,"m5.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
hsv=cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
H,S,V=cv2.split(hsv)
white=((S<60)&(V>205)).astype(np.uint8)*255
roi=np.zeros_like(white); roi[150:470,660:980]=white[150:470,660:980]
roi=cv2.morphologyEx(roi,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
n,lab,stats,cent=cv2.connectedComponentsWithStats(roi)
pts=[]
vis=img.copy()
for i in range(1,n):
    x,y,w,h,a=stats[i]
    if 15<=w<=70 and 15<=h<=70 and 300<=a<=3000:
        cx,cy=cent[i]
        pts.append((cx,cy,a,w,h))
        cv2.circle(vis,(int(cx),int(cy)),8,(0,0,255),2)
pts.sort()
for p in pts: print(f"center=({p[0]:.0f},{p[1]:.0f}) area={p[2]} size={p[3]}x{p[4]}")
print("--- 相邻间距 ---")
for a,b in zip(pts,pts[1:]):
    d=math.hypot(a[0]-b[0],a[1]-b[1])
    print(f"({a[0]:.0f},{a[1]:.0f})->({b[0]:.0f},{b[1]:.0f}) d={d:.1f}")
cv2.imencode(".png",vis)[1].tofile(os.path.join(D,"dome.png"))
