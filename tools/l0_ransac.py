# -*- coding: utf-8 -*-
# 平台外轮廓边界点 -> RANSAC拟合可见边(3条)，输出直线/交点/debug
import cv2, numpy as np, os, json
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
im=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_l0_two_shot_base.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
mask=cv2.inRange(hsv,np.array([28,25,120]),np.array([95,190,255]))
mask[hsv[:,:,0]>95]=0
mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((31,31),np.uint8))
mask=cv2.morphologyEx(mask,cv2.MORPH_OPEN,np.ones((7,7),np.uint8))
cnts,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
cnt=max(cnts,key=cv2.contourArea)
pts=cnt[:,0,:].astype(np.float64)
# 排除UI按钮带(x>890,y<130)与画布边框贴边点
keep=~((pts[:,0]>890)&(pts[:,1]<130))
pts=pts[keep]
rng=np.random.default_rng(0)
lines=[]
for _ in range(4):
    best=None
    for _t in range(2000):
        i,j=rng.choice(len(pts),2,replace=False)
        p1,p2=pts[i],pts[j]
        d=p2-p1; n=np.hypot(*d)
        if n<20: continue
        nrm=np.array([-d[1],d[0]])/n
        dist=np.abs((pts-p1)@nrm)
        inl=dist<4
        if best is None or inl.sum()>best[0]:
            best=(int(inl.sum()),p1,p2,inl)
    n_inl,p1,p2,inl=best
    if n_inl<40: break
    # 最小二乘拟合该内点集
    X=pts[inl]
    vx,vy,x0,y0=cv2.fitLine(X,cv2.DIST_L2,0,0.01,0.01).flatten()
    resid=float(np.mean(np.abs((X-[x0,y0])@np.array([-vy,vx])/np.hypot(vy,vx))))
    angle=float(np.degrees(np.arctan2(vy,vx)))
    lines.append({"vx":float(vx),"vy":float(vy),"x0":float(x0),"y0":float(y0),"n":n_inl,"resid":round(resid,2),"angle":round(angle,1),"inl_idx":np.where(inl)[0].tolist()})
    pts=pts[~inl]
    if len(pts)<60: break
dbg=im.copy()
colors=[(0,255,0),(255,0,0),(0,255,255),(255,0,255)]
for k,L in enumerate(lines):
    vx,vy,x0,y0=L["vx"],L["vy"],L["x0"],L["y0"]
    t=np.array([-2000,2000]); p1=(x0+vx*t[0],y0+vy*t[0]); p2=(x0+vx*t[1],y0+vy*t[1])
    cv2.line(dbg,(int(p1[0]),int(p1[1])),(int(p2[0]),int(p2[1])),colors[k],2)
    print(f"line{k}: angle={L['angle']} n={L['n']} resid={L['resid']} 方程: y={vy/vx:.3f}x+{y0-vy/vx*x0:.1f}")
cv2.imencode(".png",dbg)[1].tofile(os.path.join(ROOT,"out","overlay","l0new","ransac.png"))
json.dump(lines,open(os.path.join(ROOT,"out","overlay","l0new","lines.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
