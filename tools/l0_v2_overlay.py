# -*- coding: utf-8 -*-
# 纯离线：画 v2 晶格到画布(供读中心px)，并输出反算函数；不写config
import cv2, numpy as np, os, json, math
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
im=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_l0_three_shot_base.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
H,W=im.shape[:2]
O=np.array([473.2,796.6]); a=np.array([11.787,20.906]); b=np.array([-20.337,12.744])
M=np.column_stack([a,b]); Minv=np.linalg.inv(M)
vis=im.copy()
# 覆盖整个画布的晶格线：找i,j范围使线过画布
# p=O+i*a+j*b；反解边界
# 直接枚举 i,j ∈ [-40..60] 画
for i in range(-40,61):
    p0=O+i*a+(-40)*b; p1=O+i*a+(60)*b
    cv2.line(vis,tuple(p0.astype(int)),tuple(p1.astype(int)),(0,200,0),1)
for j in range(-40,61):
    p0=O+(-40)*a+j*b; p1=O+(60)*a+j*b
    cv2.line(vis,tuple(p0.astype(int)),tuple(p1.astype(int)),(0,200,0),1)
# 原点
cv2.circle(vis,tuple(O.astype(int)),5,(0,0,255),-1)
cv2.putText(vis,"O",(int(O[0])+6,int(O[1])-6),cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,0,255),2)
cv2.imencode(".png",vis)[1].tofile(os.path.join(ROOT,"out","overlay","l0three","v2_lattice_full.png"))
# 象限放大
for name,(x0,y0,x1,y1) in {"v2_q1":(0,0,460,560),"v2_q2":(445,0,905,560),"v2_q3":(0,520,460,1068),"v2_q4":(445,520,905,1068)}.items():
    q=vis[y0:y1,x0:x1]
    q=cv2.resize(q,None,fx=2,fy=2,interpolation=cv2.INTER_CUBIC)
    cv2.imencode(".png",q)[1].tofile(os.path.join(ROOT,"out","overlay","l0three",name+".png"))
print("done; |a|=%.4f |b|=%.4f"%(math.hypot(*a),math.hypot(*b)))
