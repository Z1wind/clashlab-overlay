# -*- coding: utf-8 -*-
# 三帧canvas平台边分割+Hough+区域聚类LS拟合4边；校验顶点在内/H/W；输出quad
import cv2, numpy as np, os, json, time
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
im=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_l0_three_shot_base.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
H,W=im.shape[:2]
hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
m=cv2.inRange(hsv,np.array([30,40,180]),np.array([90,150,255]))
m[hsv[:,:,0]>95]=0
m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((25,25),np.uint8))
cnts,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
cnt=max(cnts,key=cv2.contourArea)
edge=np.zeros(m.shape,np.uint8); cv2.drawContours(edge,[cnt],-1,255,2)
lines=cv2.HoughLinesP(edge,1,np.pi/1800,threshold=40,minLineLength=80,maxLineGap=25)
groups={"T_R":[],"R_B":[],"B_L":[],"L_T":[]}
for l in lines.reshape(-1,4):
    x1,y1,x2,y2=map(int,l)
    dx,dy=x2-x1,y2-y1
    if abs(dx)<5: continue
    ang=np.degrees(np.arctan2(dy,dx)); mx,my=(x1+x2)/2,(y1+y2)/2
    # 区域: 上边带(y<H*0.35) / 下边带(y>H*0.65) / 左带(x<W*0.35) / 右带(x>W*0.65)
    if my<H*0.35 and mx>W*0.45 and 15<ang<55: groups["T_R"].append((x1,y1,x2,y2))
    elif my>H*0.65 and mx>W*0.45 and -55<ang<-15: groups["R_B"].append((x1,y1,x2,y2))
    elif my>H*0.65 and mx<W*0.55 and 15<ang<55: groups["B_L"].append((x1,y1,x2,y2))
    elif my<H*0.35 and mx<W*0.55 and -55<ang<-15: groups["L_T"].append((x1,y1,x2,y2))
def fit(g):
    pts=[]
    for x1,y1,x2,y2 in g: pts.append((x1,y1)); pts.append((x2,y2))
    P=np.array(pts,float)
    vx,vy,x0,y0=cv2.fitLine(P,cv2.DIST_L2,0,0.01,0.01).flatten()
    nrm=np.array([-vy,vx])/np.hypot(vy,vx)
    resid=float(np.mean(np.abs((P-[x0,y0])@nrm)))
    return vx,vy,x0,y0,resid,len(g)
fits={}
for k,g in groups.items():
    if len(g)>=3:
        fits[k]=fit(g)
        print(k,"n=",len(g),"resid=",round(fits[k][4],2),"ang=",round(np.degrees(np.arctan2(fits[k][1],fits[k][0])),1))
def intersect(f1,f2):
    vx1,vy1,x01,y01=f1[:4]; vx2,vy2,x02,y02=f2[:4]
    A=np.array([[vx1,-vx2],[vy1,-vy2]]); b=np.array([x02-x01,y02-y01])
    t=np.linalg.solve(A,b); return np.array([x01+vx1*t[0],y01+vy1*t[0]])
T=intersect(fits["T_R"],fits["L_T"])
R=intersect(fits["T_R"],fits["R_B"])
B=intersect(fits["R_B"],fits["B_L"])
L=intersect(fits["B_L"],fits["L_T"])
Hd=np.hypot(*(T-B)); Wd=np.hypot(*(R-L))
print("T",T,"R",R,"B",B,"L",L)
print("H=",round(Hd,1),"W=",round(Wd,1),"H/W=",round(Hd/Wd,3))
inside=all(0<=p[0]<=W and 0<=p[1]<=H for p in [T,R,B,L])
print("vertices inside canvas:",inside)
dbg=im.copy()
for k,f,col in [("T_R",fits["T_R"],(0,255,0)),("R_B",fits["R_B"],(255,0,255)),("B_L",fits["B_L"],(0,255,255)),("L_T",fits["L_T"],(255,0,0))]:
    vx,vy,x0,y0=f[:4]
    t=np.array([-3000,3000])
    cv2.line(dbg,(int(x0+vx*t[0]),int(y0+vy*t[0])),(int(x0+vx*t[1]),int(y0+vy*t[1])),col,2)
for nm,p,col in [("T",T,(0,255,0)),("R",R,(255,0,255)),("B",B,(255,0,0)),("L",L,(0,255,255))]:
    cv2.circle(dbg,tuple(p.astype(int)),9,col,-1)
    cv2.putText(dbg,f"{nm}({p[0]:.0f},{p[1]:.0f})",tuple(p.astype(int)+[12,-12]),cv2.FONT_HERSHEY_SIMPLEX,0.6,col,2)
cv2.imencode(".png",dbg)[1].tofile(os.path.join(ROOT,"out","overlay","l0three","quad3.png"))
json.dump({"T":T.tolist(),"R":R.tolist(),"B":B.tolist(),"L":L.tolist(),"H":Hd,"W":Wd,"HW":Hd/Wd,"inside":bool(inside)},open(os.path.join(ROOT,"out","overlay","l0three","quad3.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
