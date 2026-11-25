# -*- coding: utf-8 -*-
# v15_chain_stitch2.py — UI掩码+RANSAC仿射链平移估计。新文件。
import os, cv2, numpy as np, json
R = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\_recon"
M = os.path.join(R,"max")
order=[]
for r in range(9):
    seq=list(range(6)) if r%2==0 else list(range(5,-1,-1))
    for c in seq: order.append((r,c))

def load(c,r):
    return cv2.imdecode(np.fromfile(os.path.join(M,f"b_c{c}r{r}.png"),dtype=np.uint8),1)

H,W=720,1280
mask=np.full((H,W),255,np.uint8)
mask[0:260,0:330]=0          # 左上资源条/名牌
mask[680:720,:]=0           # 底部按钮条
mask[130:410,0:130]=0       # 左盾牌
mask[560:720,1000:1280]=0  # 右下面板

orb=cv2.ORB_create(1200)
bf=cv2.BFMatcher(cv2.NORM_HAMMING,crossCheck=False)
imgs=[load(c,r) for r,c in order]

def motion(a,b):
    ga=cv2.cvtColor(a,cv2.COLOR_BGR2GRAY); gb=cv2.cvtColor(b,cv2.COLOR_BGR2GRAY)
    ka,da=orb.detectAndCompute(ga,mask)
    kb,db=orb.detectAndCompute(gb,mask)
    if da is None or db is None or len(ka)<10 or len(kb)<10: return None,0
    knn=bf.knnMatch(da,db,k=2)
    good=[m for m,n in knn if m.distance<0.8*n.distance]
    if len(good)<15: return None,len(good)
    pa=np.float32([ka[m.queryIdx].pt for m in good])
    pb=np.float32([kb[m.trainIdx].pt for m in good])
    Mm,inl=cv2.estimateAffinePartial2D(pa,pb,None,cv2.RANSAC,3.0)
    if Mm is None: return None,len(good)
    dx=float(Mm[0,2]); dy=float(Mm[1,2])
    nin=int(inl.sum()) if inl is not None else len(good)
    # 残差：内点配对距离中位
    if nin>=10:
        good_in=[g for g,i in zip(good,inl.ravel()) if i]
        pa2=np.float32([ka[g.queryIdx].pt for g in good_in])
        pb2=np.float32([kb[g.trainIdx].pt for g in good_in])
        res=float(np.median(np.linalg.norm((pb2-pa2)-[dx,dy],axis=1)))
    else: res=None
    return (dx,dy,res),nin

pos=[(0.0,0.0)]; edges=[]
for i in range(1,len(imgs)):
    m,nin=motion(imgs[i-1],imgs[i])
    if m is None: dx=dy=0.0;res=None;ok=False
    else: dx,dy,res=m;ok=nin>=10
    edges.append({"from":order[i-1],"to":order[i],"dx":round(dx,2),"dy":round(dy,2),
                  "inliers":nin,"residual_px":None if res is None else round(res,2),"ok":ok})
    px,py=pos[-1]; pos.append((px+dx,py+dy))

minx=min(p[0] for p in pos);miny=min(p[1] for p in pos)
pos=[(x-minx,y-miny) for x,y in pos]
maxx=max(x+W for x,_ in pos);maxy=max(y+H for _,y in pos)
canvas=np.full((int(maxy),int(maxx),3),18,np.uint8)
for i,im in enumerate(imgs):
    x,y=pos[i];xi,yi=int(round(x)),int(round(y))
    h,w=im.shape[:2]
    canvas[yi:yi+h,xi:xi+w]=im[:min(h,canvas.shape[0]-yi),:min(w,canvas.shape[1]-xi)]
cv2.imencode(".png",canvas)[1].tofile(os.path.join(R,"recon_full_max_raw.png"))
report={"method":"chain ORB + RANSAC affine, UI masked","blocks":len(imgs),"edges":edges,"canvas":[int(maxx),int(maxy)]}
with open(os.path.join(R,"stitch_max_report.json"),"w",encoding="utf-8") as f: json.dump(report,f,ensure_ascii=False,indent=2)
print("canvas",canvas.shape)
for e in edges: print(e["from"],"->",e["to"],"dx",e["dx"],"dy",e["dy"],"in",e["inliers"],"res",e["residual_px"])
