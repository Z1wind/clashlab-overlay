# -*- coding: utf-8 -*-
# 纯离线：检测黄色金币气泡(金仓上方)与紫色圣水气泡质心，输出候选列表；不写config
import cv2, numpy as np, os
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
im=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_l0_three_shot_base.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
# 金黄气泡
mask_g=cv2.inRange(hsv,np.array([18,120,150]),np.array([40,255,255]))
# 紫色气泡
mask_p=cv2.inRange(hsv,np.array([125,80,120]),np.array([165,255,255]))
for label,mask in [("GOLD",mask_g),("PURPLE",mask_p)]:
    n,lab,stats,cent=cv2.connectedComponentsWithStats(mask)
    print(f"--- {label} ---")
    for i in range(1,n):
        area=stats[i,cv2.CC_STAT_AREA]
        if area<60: continue
        x,y,w,h=stats[i,:4]
        cx,cy=cent[i]
        print(f"blob area={area:5d} bbox=({x},{y},{w},{h}) centroid=({cx:.0f},{cy:.0f})")
# 标注图
vis=im.copy()
for label,mask,col in [("GOLD",mask_g,(0,215,255)),("PURPLE",mask_p,(255,0,255))]:
    n,lab,stats,cent=cv2.connectedComponentsWithStats(mask)
    for i in range(1,n):
        if stats[i,cv2.CC_STAT_AREA]<60: continue
        cx,cy=cent[i]
        cv2.circle(vis,(int(cx),int(cy)),8,col,2)
        cv2.putText(vis,f"{label[0]}",(int(cx)+9,int(cy)-9),cv2.FONT_HERSHEY_SIMPLEX,0.4,col,1)
cv2.imencode(".png",vis)[1].tofile(os.path.join(ROOT,"out","overlay","l0three","bubbles.png"))
print("done")
