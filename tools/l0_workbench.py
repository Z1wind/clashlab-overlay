# -*- coding: utf-8 -*-
# 纯离线测量工作台：人工录入点，① 底面边px/格；② v2反算ij vs 人工整数格位
# 用法：编辑 POINTS/FOOTPRINTS，运行后打印结果并出标注图
import cv2, numpy as np, os, math, json, datetime
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
im=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_l0_three_shot_base.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
H,W=im.shape[:2]
# ---- v2 晶格(只读) ----
O=np.array([473.2,796.6]); a=np.array([11.787,20.906]); b=np.array([-20.337,12.744])
M=np.column_stack([a,b]); Minv=np.linalg.inv(M)
def invert(p):
    return (np.array(p)-O)@Minv.T

# ---- ① 底面直测：name, 两个对角/边端点(画布px), 格边数 ----
# 边 = 两点欧氏距离 / 格数
FOOTPRINTS=[
    # name, p1, p2(同一条边两端), tiles
    ("法师塔SE_紫环",(628,632),(696,692),3),
    ("金仓NE_基座",(500,182),(572,218),3),
    ("金仓SW_基座",(178,572),(244,612),3),
    ("金仓SE_基座",(612,608),(682,648),3),
    ("金仓S_基座",(368,724),(436,762),3),
]
# ---- ② 中心读数(画布px) + 人工整数格位(独立数出) ----
# name, center, manual_ij=(i,j)
CENTERS=[
    ("紫圣水E",(837,479),(0,0)),
]
vis=im.copy()
print("=== ① 底面 px/格 直测 ===")
res=[]
for nm,p1,p2,t in FOOTPRINTS:
    d=math.hypot(p2[0]-p1[0],p2[1]-p1[1])
    ppt=d/t
    res.append((nm,d,t,ppt))
    print(f"{nm:14s} edge={d:6.1f}px /{t} = {ppt:5.2f} px/格")
    cv2.circle(vis,p1,4,(0,0,255),-1); cv2.circle(vis,p2,4,(0,0,255),-1)
    cv2.line(vis,p1,p2,(0,0,255),1)
if res:
    mean=sum(r[3] for r in res)/len(res)
    print(f"mean={mean:.2f} vs 24.0 偏差={(mean/24.0-1)*100:+.2f}%")
print()
print("=== ② v2 反算格位 ===")
for nm,c,ij in CENTERS:
    ij2=invert(c)
    print(nm,c,"inv=",np.round(ij2,2),"manual=",ij)
cv2.imencode(".png",vis)[1].tofile(os.path.join(ROOT,"out","overlay","l0three","workbench.png"))
print("done")
