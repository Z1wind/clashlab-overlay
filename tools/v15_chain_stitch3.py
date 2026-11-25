# -*- coding: utf-8 -*-
# v15_chain_stitch3.py — 命令几何摆放(横600/纵240)，ORB残差仅作缝质量。新文件。
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
mask[0:260,0:330]=0; mask[680:720,:]=0; mask[130:410,0:130]=0; mask[560:720,1000:1280]=0
orb=cv2.ORB_create(1200); bf=cv2.BFMatcher(cv2.NORM_HAMMING,crossCheck=False)
imgs=[load(c,r) for r,c in order]

def orb_residual(a,b):
    ga=cv2.cvtColor(a,cv2.COLOR_BGR2GRAY);gb=cv2.cvtColor(b,cv2.COLOR_BGR2GRAY)
    ka,da=orb.detectAndCompute(ga,mask);kb,db=orb.detectAndCompute(gb,mask)
    if da is None or db is None: return None,0
    knn=bf.knnMatch(da,db,k=2)
    good=[m for m,n in knn if m.distance<0.8*n.distance]
    if len(good)<15: return None,len(good)
    pa=np.float32([ka[m.queryIdx].pt for m in good]);pb=np.float32([kb[m.trainIdx].pt for m in good])
    Mm,inl=cv2.estimateAffinePartial2D(pa,pb,None,cv2.RANSAC,3.0)
    if Mm is None: return None,len(good)
    nin=int(inl.sum()) if inl is not None else len(good)
    good_in=[g for g,i in zip(good,inl.ravel()) if i]
    pa2=np.float32([ka[g.queryIdx].pt for g in good_in]);pb2=np.float32([kb[g.trainIdx].pt for g in good_in])
    res=float(np.median(np.linalg.norm((pb2-pa2)-[Mm[0,2],Mm[1,2]],axis=1)))
    return res,nin

# 命令几何：水平步 600，行南移 240
pos=[(0.0,0.0)]; edges=[]
for i in range(1,len(imgs)):
    (pr,pc),(cr,cc)=order[i-1],order[i]
    if pr==cr:
        # 同横行：东扫 r偶 步-600；西扫 r奇 步+600
        dx=-600.0 if pr%2==0 else 600.0; dy=0.0
    else:
        dx=0.0; dy=-240.0
    px,py=pos[-1]; pos.append((px+dx,py+dy))
    res,nin=orb_residual(imgs[i-1],imgs[i])
    edges.append({"from":order[i-1],"to":order[i],"cmd_dx":dx,"cmd_dy":dy,
                  "orb_residual_px":None if res is None else round(res,2),"orb_inliers":nin})

minx=min(p[0] for p in pos);miny=min(p[1] for p in pos)
pos=[(x-minx,y-miny) for x,y in pos]
maxx=max(x+W for x,_ in pos);maxy=max(y+H for _,y in pos)
canvas=np.full((int(maxy),int(maxx),3),18,np.uint8)
for i,im in enumerate(imgs):
    x,y=pos[i];xi,yi=int(round(x)),int(round(y));h,w=im.shape[:2]
    canvas[yi:yi+h,xi:xi+w]=im[:min(h,canvas.shape[0]-yi),:min(w,canvas.shape[1]-xi)]
cv2.imencode(".png",canvas)[1].tofile(os.path.join(R,"recon_full_max_raw.png"))
worst=max((e["orb_residual_px"] or 0) for e in edges)
report={"method":"command-geometry grid (step 600h/240v) + ORB residual QC","blocks":len(imgs),
        "canvas":[int(maxx),int(maxy)],"max_orb_residual_px":worst,"edges":edges}
with open(os.path.join(R,"stitch_max_report.json"),"w",encoding="utf-8") as f: json.dump(report,f,ensure_ascii=False,indent=2)
print("canvas",canvas.shape,"worst orb residual",worst)
