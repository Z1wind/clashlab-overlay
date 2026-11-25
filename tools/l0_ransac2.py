# -*- coding: utf-8 -*-
# mask3_c边界 -> 方向约束RANSAC(斜率0.35~0.75, 两类符号) -> LS拟合可见边
import cv2, numpy as np, os, json
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
im=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_l0_two_shot_base.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
m=cv2.inRange(hsv,np.array([30,40,180]),np.array([90,150,255]))
m[hsv[:,:,0]>95]=0
m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((25,25),np.uint8))
cnts,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
cnt=max(cnts,key=cv2.contourArea)
pts=cnt[:,0,:].astype(np.float64)
H,W=im.shape[:2]
# 排除贴画布边框的点
border=(pts[:,0]<4)|(pts[:,0]>W-4)|(pts[:,1]<4)|(pts[:,1]>H-4)
pts=pts[~border]
# 排除UI按钮区
pts=pts[~((pts[:,0]>890)&(pts[:,1]<140))]
rng=np.random.default_rng(1)
lines=[]
remain=pts.copy()
for _ in range(4):
    best=None
    for _t in range(4000):
        i,j=rng.choice(len(remain),2,replace=False)
        p1,p2=remain[i],remain[j]
        d=p2-p1; n=np.hypot(*d)
        if n<30: continue
        vx,vy=d/n
        slope=vy/vx if abs(vx)>1e-3 else 9
        if not (0.30<abs(slope)<0.85): continue
        nrm=np.array([-vy,vx])
        dist=np.abs((remain-p1)@nrm)
        inl=dist<5
        if best is None or inl.sum()>best[0]:
            best=(int(inl.sum()),p1,p2,inl,slope)
    if best is None or best[0]<30: break
    n_inl,p1,p2,inl,slope=best
    X=remain[inl]
    vx,vy,x0,y0=cv2.fitLine(X,cv2.DIST_L2,0,0.01,0.01).flatten()
    resid=float(np.mean(np.abs((X-[x0,y0])@np.array([-vy,vx])/np.hypot(vy,vx))))
    angle=float(np.degrees(np.arctan2(vy,vx)))
    lines.append({"vx":float(vx),"vy":float(vy),"x0":float(x0),"y0":float(y0),"n":n_inl,"resid":round(resid,2),"angle":round(angle,1),"slope":round(float(vy/vx),3)})
    remain=remain[~inl]
dbg=im.copy()
colors=[(0,255,0),(255,0,0),(0,255,255),(255,0,255)]
for k,L in enumerate(lines):
    vx,vy,x0,y0=L["vx"],L["vy"],L["x0"],L["y0"]
    t=np.array([-3000,3000]); p1=(x0+vx*t[0],y0+vy*t[0]); p2=(x0+vx*t[1],y0+vy*t[1])
    cv2.line(dbg,(int(p1[0]),int(p1[1])),(int(p2[0]),int(p2[1])),colors[k],2)
    print(f"line{k}: angle={L['angle']} slope={L['slope']} n={L['n']} resid={L['resid']} y={L['slope']:.3f}x+{y0-L['slope']*x0:.1f}")
cv2.imencode(".png",dbg)[1].tofile(os.path.join(ROOT,"out","overlay","l0new","ransac2.png"))
json.dump(lines,open(os.path.join(ROOT,"out","overlay","l0new","lines2.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
