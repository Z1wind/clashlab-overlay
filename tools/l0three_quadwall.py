# -*- coding: utf-8 -*-
# 围墙双族平行线：按截距聚类取最外两条，LS拟合，交点成quad；校验内/H/W
import cv2, numpy as np, os, json, time
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
im=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_l0_three_shot_base.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
H,W=im.shape[:2]
hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
m=cv2.inRange(hsv,np.array([12,35,150]),np.array([32,150,245]))
m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))
cnts,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
edge=np.zeros(m.shape,np.uint8)
for c in cnts:
    if cv2.contourArea(c)>200: cv2.drawContours(edge,[c],-1,255,1)
lines=cv2.HoughLinesP(edge,1,np.pi/1800,threshold=60,minLineLength=120,maxLineGap=30)
pos=[]; neg=[]
for l in lines.reshape(-1,4):
    x1,y1,x2,y2=map(int,l); dx,dy=x2-x1,y2-y1
    if abs(dx)<8: continue
    ang=np.degrees(np.arctan2(dy,dx))
    length=np.hypot(dx,dy)
    if 25<ang<50: pos.append((x1,y1,x2,y2,length))
    elif -50<ang<-25: neg.append((x1,y1,x2,y2,length))
def cluster_outer(segs,slope):
    # 截距 b=y-slope*x；按排序二分取两端簇(各>80%长度阈值)
    B=[(y1-slope*x1+y2-slope*x2)/2 for x1,y1,x2,y2,_ in segs]
    order=np.argsort(B)
    bs=np.array(B)[order]; sg=np.array(segs)[order]
    # 端点簇: 最小b簇与最大b簇, 间距>60px才算两条
    lo=bs[0]; hi=bs[-1]
    lo_m=[i for i,b in enumerate(bs) if abs(b-lo)<50]
    hi_m=[i for i,b in enumerate(bs) if abs(b-hi)<50]
    return sg[lo_m],sg[hi_m]
def lsfit(g):
    pts=[]
    for x1,y1,x2,y2,_ in g: pts.append((x1,y1)); pts.append((x2,y2))
    P=np.array(pts,float)
    vx,vy,x0,y0=cv2.fitLine(P,cv2.DIST_L2,0,0.01,0.01).flatten()
    nrm=np.array([-vy,vx])/np.hypot(vy,vx)
    resid=float(np.mean(np.abs((P-[x0,y0])@nrm)))
    return vx,vy,x0,y0,resid,len(g)
plo_hi,plo_lo=cluster_outer(pos,0.73)   # +族: 上侧(T-R)/下侧(B-L)
pne_hi,pne_lo=cluster_outer(neg,-0.73)  # -族: 右(R-B)/左(L-T)
f_TR=lsfit(plo_hi); f_BL=lsfit(plo_lo)
f_RB=lsfit(pne_hi); f_LT=lsfit(pne_lo)
for nm,f in [("TR",f_TR),("BL",f_BL),("RB",f_RB),("LT",f_LT)]:
    print(nm,"n=",f[5],"resid=",round(f[4],2),"ang=",round(np.degrees(np.arctan2(f[1],f[0])),1))
def intersect(f1,f2):
    vx1,vy1,x01,y01=f1[:4]; vx2,vy2,x02,y02=f2[:4]
    A=np.array([[vx1,-vx2],[vy1,-vy2]]); b=np.array([x02-x01,y02-y01])
    t=np.linalg.solve(A,b); return np.array([x01+vx1*t[0],y01+vy1*t[0]])
T=intersect(f_TR,f_LT); R=intersect(f_TR,f_RB); B=intersect(f_BL,f_RB); L=intersect(f_BL,f_LT)
Hd=np.hypot(*(T-B)); Wd=np.hypot(*(R-L))
print("T",T,"R",R,"B",B,"L",L)
print("H=",round(Hd,1),"W=",round(Wd,1),"H/W=",round(Hd/Wd,3))
inside=all(0<=p[0]<=W and 0<=p[1]<=H for p in [T,R,B,L])
print("inside:",inside)
dbg=im.copy()
for f,col in [(f_TR,(0,255,0)),(f_BL,(0,255,255)),(f_RB,(255,0,255)),(f_LT,(255,0,0))]:
    vx,vy,x0,y0=f[:4]; t=np.array([-3000,3000])
    cv2.line(dbg,(int(x0+vx*t[0]),int(y0+vy*t[0])),(int(x0+vx*t[1]),int(y0+vy*t[1])),col,2)
for nm,p,col in [("T",T,(0,255,0)),("R",R,(255,0,255)),("B",B,(255,0,0)),("L",L,(0,255,255))]:
    cv2.circle(dbg,tuple(p.astype(int)),9,col,-1)
    cv2.putText(dbg,f"{nm}({p[0]:.0f},{p[1]:.0f})",tuple(p.astype(int)+[12,-12]),cv2.FONT_HERSHEY_SIMPLEX,0.6,col,2)
cv2.imencode(".png",dbg)[1].tofile(os.path.join(ROOT,"out","overlay","l0three","quad_wall.png"))
json.dump({"T":T.tolist(),"R":R.tolist(),"B":B.tolist(),"L":L.tolist(),"H":float(Hd),"W":float(Wd),"HW":float(Hd/Wd),"inside":bool(inside),
 "resid":{"TR":f_TR[4],"BL":f_BL[4],"RB":f_RB[4],"LT":f_LT[4]}},open(os.path.join(ROOT,"out","overlay","l0three","quad_wall.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
