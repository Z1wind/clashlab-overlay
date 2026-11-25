# -*- coding: utf-8 -*-
# 三边拟合(A=NE/B=NW/C=SW) + 中点不变量外推R；输出顶点/直线/残差/ratio；写quad json
import cv2, numpy as np, os, json, time
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT=os.path.join(ROOT,"out","overlay","l0new")
im=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_l0_two_shot_base.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
m=cv2.inRange(hsv,np.array([30,40,180]),np.array([90,150,255]))
m[hsv[:,:,0]>95]=0
m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((25,25),np.uint8))
cnts,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
cnt=max(cnts,key=cv2.contourArea)
edge=np.zeros(m.shape,np.uint8); cv2.drawContours(edge,[cnt],-1,255,2)
lines=cv2.HoughLinesP(edge,1,np.pi/1800,threshold=40,minLineLength=60,maxLineGap=20)
groups={"A_NE":[],"B_NW":[],"C_SW":[],"D_SE":[]}
for l in lines.reshape(-1,4):
    x1,y1,x2,y2=map(int,l)
    dx,dy=x2-x1,y2-y1
    if abs(dx)<5: continue
    ang=np.degrees(np.arctan2(dy,dx))
    mx,my=(x1+x2)/2,(y1+y2)/2
    # 区域+角度双重聚类
    if my<360 and mx>480 and 20<ang<50: groups["A_NE"].append((x1,y1,x2,y2))
    elif my<260 and mx<420 and -50<ang<-20: groups["B_NW"].append((x1,y1,x2,y2))
    elif my>500 and mx<400 and 30<ang<55: groups["C_SW"].append((x1,y1,x2,y2))
    elif my>500 and mx>500 and -50<ang<-25: groups["D_SE"].append((x1,y1,x2,y2))

def fit(g):
    pts=[]
    for x1,y1,x2,y2 in g:
        pts.append((x1,y1)); pts.append((x2,y2))
    P=np.array(pts,float)
    vx,vy,x0,y0=cv2.fitLine(P,cv2.DIST_L2,0,0.01,0.01).flatten()
    nrm=np.array([-vy,vx])/np.hypot(vy,vx)
    resid=float(np.mean(np.abs((P-[x0,y0])@nrm)))
    return vx,vy,x0,y0,resid,P

fits={}
for k in ["A_NE","B_NW","C_SW","D_SE"]:
    if groups[k]:
        fits[k]=fit(groups[k])
        print(k,"n_seg=",len(groups[k]),"resid=",round(fits[k][4],2),"y=",fits[k][3]/fits[k][2] if abs(fits[k][0])>1e-3 else 0)

def intersect(f1,f2):
    vx1,vy1,x01,y01=f1[:4]; vx2,vy2,x02,y02=f2[:4]
    A=np.array([[vx1,-vx2],[vy1,-vy2]])
    b=np.array([x02-x01,y02-y01])
    t=np.linalg.solve(A,b)
    return np.array([x01+vx1*t[0],y01+vy1*t[0]])

T=intersect(fits["A_NE"],fits["B_NW"])
L=intersect(fits["B_NW"],fits["C_SW"])
Bv=intersect(fits["C_SW"],fits["D_SE"]) if "D_SE" in fits else None
# 三边(A,B,C)拟合：T=A∩B, L=B∩C; B顶点由C与(由中点反推)先取D检查
# 中点不变量 R = T + Bv - L；若Bv由D交得
if Bv is None:
    # 用C线+竖直对顶关系无法定B；用D观测段参与拟合
    raise SystemExit("need D")
R=T+Bv-L
H=np.hypot(*(T-Bv)); W=np.hypot(*(L-R))
print("T=",T,"L=",L,"B=",Bv,"R=",R)
print("H=",round(H,1),"W=",round(W,1),"H/W=",round(H/W,3))
# D观测段到预测D线(Bv-R)残差检查
vD=R-Bv; nrmD=np.array([-vD[1],vD[0]])/np.hypot(*vD)
if "D_SE" in fits:
    Pd=fits["D_SE"][5]
    d=np.abs((Pd-Bv)@nrmD)
    print("D观测点到预测D线残差=",round(float(np.mean(d)),2),"px n=",len(Pd))
# A/B/C拟合残差汇总
fit_resid={k:round(fits[k][4],2) for k in ["A_NE","B_NW","C_SW"]}
# debug
dbg=im.copy()
col={"A_NE":(0,255,0),"B_NW":(255,0,0),"C_SW":(0,255,255),"D_SE":(255,0,255)}
for k,f in fits.items():
    vx,vy,x0,y0=f[:4]
    t=np.array([-3000,3000])
    cv2.line(dbg,(int(x0+vx*t[0]),int(y0+vy*t[0])),(int(x0+vx*t[1]),int(y0+vy*t[1])),col[k],2)
for name,p,c in [("T",T,(0,255,0)),("R",R,(255,0,255)),("B",Bv,(255,0,0)),("L",L,(0,255,255))]:
    cv2.circle(dbg,tuple(p.astype(int)),8,c,-1)
    cv2.putText(dbg,f"{name}({p[0]:.0f},{p[1]:.0f})",tuple(p.astype(int)+np.array([10,-10])),cv2.FONT_HERSHEY_SIMPLEX,0.6,c,2)
cv2.imencode(".png",dbg)[1].tofile(os.path.join(OUT,"quad_fit.png"))

quad={"T":[round(float(T[0]),1),round(float(T[1]),1)],"R":[round(float(R[0]),1),round(float(R[1]),1)],"B":[round(float(Bv[0]),1),round(float(Bv[1]),1)],"L":[round(float(L[0]),1),round(float(L[1]),1)]}
cfg={
 "quad":quad,
 "canvas":[950,773],
 "tile_px":24.0,"tile_px_range":[23.8,24.4],
 "source":"L0_two_shot+3edge_fit",
 "shots":2,
 "overlap_tiles":13.6,
 "seam_resid":0.037,
 "fit_resid":fit_resid,
 "diag_H_px":round(float(H),1),"diag_W_px":round(float(W),1),"HW_ratio":round(float(H/W),3),
 "ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
}
os.makedirs(os.path.dirname(os.path.join(ROOT,"config","view_quads.json")),exist_ok=True)
json.dump(cfg,open(os.path.join(ROOT,"config","view_quads.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("written view_quads.json")
