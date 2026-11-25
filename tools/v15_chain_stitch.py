# -*- coding: utf-8 -*-
# v15_chain_stitch.py — 捕获链 ORB 平移估计 + 累积摆放（无网格先验）。新文件。
import os, cv2, numpy as np, json
R = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\_recon"
M = os.path.join(R,"max")

# 捕获顺序：r0 东扫; r1 西扫; r2 东; r3 西; r4 东; r5 西; r6 东; r7 西; r8 东
order=[]
for r in range(9):
    if r%2==0:
        seq=list(range(6))
    else:
        seq=list(range(5,-1,-1))
    for c in seq:
        order.append((r,c))

def load(c,r):
    p=os.path.join(M,f"b_c{c}r{r}.png")
    return cv2.imdecode(np.fromfile(p,dtype=np.uint8),1)

orb=cv2.ORB_create(800)
bf=cv2.BFMatcher(cv2.NORM_HAMMING,crossCheck=False)
imgs=[load(c,r) for r,c in order]
H,W=imgs[0].shape[:2]

def motion(a,b):
    ga=cv2.cvtColor(a,cv2.COLOR_BGR2GRAY); gb=cv2.cvtColor(b,cv2.COLOR_BGR2GRAY)
    ka,da=orb.detectAndCompute(ga,None); kb,db=orb.detectAndCompute(gb,None)
    if da is None or db is None or len(ka)<10 or len(kb)<10: return None,0
    knn=bf.knnMatch(da,db,k=2)
    good=[m for m,n in knn if m.distance<0.75*n.distance]
    if len(good)<12: return None,len(good)
    pa=np.float32([ka[m.queryIdx].pt for m in good])
    pb=np.float32([kb[m.trainIdx].pt for m in good])
    d=pb-pa
    dx=float(np.median(d[:,0])); dy=float(np.median(d[:,1]))
    res=float(np.median(np.linalg.norm(d-[dx,dy],axis=1)))
    return (dx,dy,res),len(good)

pos=[(0.0,0.0)]
edges=[]
for i in range(1,len(imgs)):
    m,nin=motion(imgs[i-1],imgs[i])
    if m is None:
        dx=dy=0.0; res=None; ok=False
    else:
        dx,dy,res=m; ok=nin>=12
    edges.append({"from":order[i-1],"to":order[i],"dx":round(dx,2),"dy":round(dy,2),
                  "inliers":nin,"residual_px":None if res is None else round(res,2),"ok":ok})
    px,py=pos[-1]
    pos.append((px+dx,py+dy))

# 归一化到正坐标
minx=min(p[0] for p in pos); miny=min(p[1] for p in pos)
pos=[(x-minx,y-miny) for x,y in pos]
maxx=max(x+W for x,_ in pos); maxy=max(y+H for _,y in pos)
canvas=np.full((int(maxy),int(maxx),3),18,np.uint8)
# 捕获顺序贴：后贴覆盖先贴（链中后者更新）
for i,im in enumerate(imgs):
    x,y=pos[i]
    xi,yi=int(round(x)),int(round(y))
    canvas[yi:yi+H,xi:xi+W]=im

cv2.imencode(".png",canvas)[1].tofile(os.path.join(R,"recon_full_max_raw.png"))
report={"method":"chain ORB translation","blocks":len(imgs),"edges":edges,
        "canvas":[int(maxx),int(maxy)]}
with open(os.path.join(R,"stitch_max_report.json"),"w",encoding="utf-8") as f:
    json.dump(report,f,ensure_ascii=False,indent=2)
bad=[e for e in edges if not e["ok"]]
print("blocks",len(imgs),"canvas",canvas.shape,"bad edges",len(bad))
for e in edges: print(e["from"],"->",e["to"],"dx",e["dx"],"dy",e["dy"],"in",e["inliers"],"ok",e["ok"])
