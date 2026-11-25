# -*- coding: utf-8 -*-
# v14_fit.py — 草地 hull 分边拟合直线，交点得 quad。新文件。
import os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EN = os.path.join(ROOT, "out", "overlay", "enemy")
im = cv2.imdecode(np.fromfile(os.path.join(EN,"b14_ov1.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
m = cv2.inRange(hsv, np.array([22,20,75]), np.array([90,255,255]))
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((25,25),np.uint8))
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((13,13),np.uint8))
cnts,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
c=max(cnts,key=cv2.contourArea)
hull=cv2.convexHull(c).reshape(-1,2)
cx,cy=hull.mean(0)
ang=np.arctan2(hull[:,1]-cy,hull[:,0]-cx)
secs={"T":(np.radians(-150),np.radians(-30)),"R":(np.radians(-30),np.radians(60)),
      "B":(np.radians(60),np.radians(150)),"L":(np.radians(150),np.radians(210))}
lines={}
vis=im.copy()
for name,(a0,a1) in secs.items():
    sel=hull[(ang>=a0)&(ang<a1)]
    if len(sel)<5: print(name,"few",len(sel)); continue
    vx,vy,x0,y0=cv2.fitLine(sel,cv2.DIST_L2,0,0.01,0.01).flatten()
    lines[name]=(vx,vy,x0,y0)
    print(name,"n=",len(sel))

def inter(l1,l2):
    vx1,vy1,x1,y1=l1; vx2,vy2,x2,y2=l2
    A=np.array([[vx1,-vx2],[vy1,-vy2]])
    t=np.linalg.solve(A,[x2-x1,y2-y1])
    return (x1+t[0]*vx1, y1+t[0]*vy1)

T=inter(lines["T"],lines["L"]); R=inter(lines["T"],lines["R"]); B=inter(lines["B"],lines["R"]); L=inter(lines["B"],lines["L"])
for nm,p in [("T",T),("R",R),("B",B),("L",L)]:
    print(nm,round(p[0],1),round(p[1],1))
    cv2.circle(vis,(int(round(p[0])),int(round(p[1]))),8,(0,0,255),2)
    cv2.putText(vis,f"{nm}",(int(p[0])+8,int(p[1])),cv2.FONT_HERSHEY_SIMPLEX,0.8,(0,0,255),2)
cv2.imencode(".png",vis)[1].tofile(os.path.join(EN,"b14_fit.png"))
W=R[0]-L[0]; H=B[1]-T[1]
print("W",round(W,1),"H",round(H,1),"W/H",round(W/H,3))
