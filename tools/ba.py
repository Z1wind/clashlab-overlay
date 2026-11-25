# -*- coding: utf-8 -*-
# ba.py — blocks3 全对 ORB 匹配 → 平移全局最小二乘 → 放置 → 边残差报告
import json, os, cv2, numpy as np
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BLK=os.path.join(ROOT,"out","overlay","blocks3")
orb=cv2.ORB_create(1500)
log=json.load(open(os.path.join(BLK,"collect_log.json"),encoding="utf-8"))
files=[t["file"] for t in log["tiles"]]
imgs=[cv2.imdecode(np.fromfile(os.path.join(BLK,f),dtype=np.uint8),cv2.IMREAD_COLOR) for f in files]
N=len(imgs)
def match(a,b):
    ga=cv2.cvtColor(a,cv2.COLOR_BGR2GRAY); gb=cv2.cvtColor(b,cv2.COLOR_BGR2GRAY)
    ka,da=orb.detectAndCompute(ga,None); kb,db=orb.detectAndCompute(gb,None)
    if da is None or db is None: return None,0
    bf=cv2.BFMatcher(cv2.NORM_HAMMING)
    knn=bf.knnMatch(da,db,k=2)
    good=[m for m,n in knn if m.distance<0.75*n.distance]
    if len(good)<10: return None,len(good)
    pa=np.float32([ka[m.queryIdx].pt for m in good])
    pb=np.float32([kb[m.trainIdx].pt for m in good])
    d=pb-pa
    mx,my=np.median(d,axis=0)
    inl=np.linalg.norm(d-[mx,my],axis=1)<12
    if inl.sum()>=8: mx,my=np.median(d[inl],axis=0)
    return (float(mx),float(my)),int(inl.sum())

edges=[]
for i in range(N):
    for j in range(i+1,N):
        s,n=match(imgs[i],imgs[j])
        if s and n>=10:
            edges.append((i,j,s[0],s[1],n))
            print(f"{files[i]}-{files[j]}: dx={s[0]:.0f} dy={s[1]:.0f} n={n}")
# 线性最小二乘: 对每条边 (i,j): t_j - t_i = (dx,dy)
Ax=[]; Ay=[]; bx=[]; by=[]
for i,j,dx,dy,n in edges:
    row=np.zeros(N); row[i]=-1; row[j]=1; Ax.append(row); bx.append(dx)
    Ay.append(row.copy()); by.append(dy)
Ax=np.array(Ax); Ay=np.array(Ay); bx=np.array(bx); by=np.array(by)
# 固定 t0=0：去掉第0列
Mx=Ax[:,1:]; My=Ay[:,1:]
solx,_,_,_=np.linalg.lstsq(Mx,bx,rcond=None)
soly,_,_,_=np.linalg.lstsq(My,by,rcond=None)
t=np.zeros((N,2))
t[1:,0]=solx; t[1:,1]=soly
print("== 边残差 ==")
bad=[]
for i,j,dx,dy,n in edges:
    ex,ey=t[j]-t[i]
    r=float(np.hypot(ex-dx,ey-dy))
    flag="OK" if r<=4 else "BAD"
    if r>4: bad.append((files[i],files[j],round(r,1),n))
    print(f"{files[i]}-{files[j]}: resid={r:.1f} n={n} {flag}")
# 放置
minx,miny=t[:,0].min(),t[:,1].min()
H,W=imgs[0].shape[:2]
maxx=t[:,0].max()-minx+W; maxy=t[:,1].max()-miny+H
canvas=np.zeros((int(maxy),int(maxx),3),np.uint8)
for k,im in enumerate(imgs):
    x=int(round(t[k,0]-minx)); y=int(round(t[k,1]-miny))
    canvas[y:y+H,x:x+W]=im
out=os.path.join(ROOT,"out","overlay","v6_stitched_base.png")
cv2.imencode(".png",canvas)[1].tofile(out)
json.dump({"bad":bad,"t":t.tolist()},open(os.path.join(BLK,"ba_report.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("BAD:",bad); print("canvas",canvas.shape)
