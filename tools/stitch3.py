# -*- coding: utf-8 -*-
# stitch3.py — blocks3 ORB链放置；两两重叠 ORB 中位平移 vs 期望偏移，残差>4px 报BAD
import json, os, cv2, numpy as np
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BLK=os.path.join(ROOT,"out","overlay","blocks3")
log=json.load(open(os.path.join(BLK,"collect_log.json"),encoding="utf-8"))
orb=cv2.ORB_create(1200)
items=[]; cumx=cumy=0.0
for t in log["tiles"]:
    im=cv2.imdecode(np.fromfile(os.path.join(BLK,t["file"]),dtype=np.uint8),cv2.IMREAD_COLOR)
    cumx+=t["dx"]; cumy+=t["dy"]
    items.append((t["file"],im,cumx,cumy))
minx=min(i[2] for i in items); miny=min(i[3] for i in items)
H,W=items[0][1].shape[:2]
maxx=max(i[2]-minx+W for i in items); maxy=max(i[3]-miny+H for i in items)
canvas=np.zeros((int(maxy),int(maxx),3),np.uint8)
placed=[]
for f,im,cx,cy in items:
    x=int(round(cx-minx)); y=int(round(cy-miny))
    canvas[y:y+H,x:x+W]=im
    placed.append((f,x,y,im))

def orb_shift(a,b):
    ga=cv2.cvtColor(a,cv2.COLOR_BGR2GRAY); gb=cv2.cvtColor(b,cv2.COLOR_BGR2GRAY)
    ka,da=orb.detectAndCompute(ga,None); kb,db=orb.detectAndCompute(gb,None)
    if da is None or db is None: return None,0
    bf=cv2.BFMatcher(cv2.NORM_HAMMING)
    knn=bf.knnMatch(da,db,k=2)
    good=[m for m,n in knn if m.distance<0.75*n.distance]
    if len(good)<8: return None,len(good)
    pa=np.float32([ka[m.queryIdx].pt for m in good])
    pb=np.float32([kb[m.trainIdx].pt for m in good])
    d=pb-pa; mx,my=np.median(d,axis=0)
    inl=np.linalg.norm(d-[mx,my],axis=1)<10
    if inl.sum()>=6: mx,my=np.median(d[inl],axis=0)
    return (float(mx),float(my)),int(inl.sum())

print("== 重叠对 ORB 残差 ==")
bad=[]
for i in range(len(placed)):
    fi,xi,yi,A=placed[i]
    for j in range(i+1,len(placed)):
        fj,xj,yj,B=placed[j]
        ox0=max(xi,xj); ox1=min(xi+W,xj+W); oy0=max(yi,yj); oy1=min(yi+H,yj+H)
        ow,oh=ox1-ox0,oy1-oy0
        if ow>=80 and oh>=80:
            As=A[oy0-yi:oy1-yi,ox0-xi:ox1-xi]
            Bs=B[oy0-yj:oy1-yj,ox0-xj:ox1-xj]
            s,n=orb_shift(As,Bs)
            if s is None:
                print(f"{fi}<->{fj}: ov{ow}x{oh} no-match n={n}")
                continue
            ex,ey=xj-xi,yj-yi
            rx,ry=s[0]-ex,s[1]-ey
            err=float(np.hypot(rx,ry))
            flag="OK" if err<=4 else "BAD"
            if err>4: bad.append((fi,fj,round(err,1),n))
            print(f"{fi}<->{fj}: ov{ow}x{oh} exp=({ex},{ey}) meas=({s[0]:.0f},{s[1]:.0f}) resid={err:.1f} n={n} {flag}")
out=os.path.join(ROOT,"out","overlay","v6_stitched_base.png")
cv2.imencode(".png",canvas)[1].tofile(out)
json.dump({"bad":bad},open(os.path.join(BLK,"stitch_report.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("BAD:",bad)
print("canvas",canvas.shape)
