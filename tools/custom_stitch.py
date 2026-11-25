# -*- coding: utf-8 -*-
# custom_stitch.py — 按实测累积偏移直接放置；两两重叠条带相位相关残差报告
import json, os, cv2, numpy as np
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BLK=os.path.join(ROOT,"out","overlay","blocks")
log=json.load(open(os.path.join(BLK,"collect_log.json"),encoding="utf-8"))
items=[]
for t in log["tiles"]:
    im=cv2.imdecode(np.fromfile(os.path.join(BLK,t["file"]),dtype=np.uint8),cv2.IMREAD_COLOR)
    items.append((t["file"],im,t["cx"],t["cy"]))
minx=min(i[2] for i in items); miny=min(i[3] for i in items)
H,W=items[0][1].shape[:2]
maxx=max(i[2]-minx+W for i in items); maxy=max(i[3]-miny+H for i in items)
canvas=np.zeros((int(maxy),int(maxx),3),np.uint8)
placed=[]
for f,im,cx,cy in items:
    x=int(round(cx-minx)); y=int(round(cy-miny))
    canvas[y:y+H,x:x+W]=im
    placed.append((f,x,y))

def pc(a,b):
    ga=cv2.cvtColor(a,cv2.COLOR_BGR2GRAY).astype(np.float64)
    gb=cv2.cvtColor(b,cv2.COLOR_BGR2GRAY).astype(np.float64)
    win=cv2.createHanningWindow((ga.shape[1],ga.shape[0]),cv2.CV_64F)
    (dx,dy),r=cv2.phaseCorrelate(ga,gb,win)
    return dx,dy,r

print("== 两两重叠残差 ==")
bad=[]
for i in range(len(placed)):
    fi,xi,yi=placed[i]
    Ai=items[i][1]
    for j in range(i+1,len(placed)):
        fj,xj,yj=placed[j]
        ox0=max(xi,xj); ox1=min(xi+W,xj+W)
        oy0=max(yi,yj); oy1=min(yi+H,yj+H)
        ow,oh=ox1-ox0,oy1-oy0
        if ow>=60 and oh>=60:
            A=Ai[oy0-yi:oy1-yi,ox0-xi:ox1-xi]
            Bj=items[j][1]
            B=Bj[oy0-yj:oy1-yj,ox0-xj:ox1-xj]
            dx,dy,r=pc(A,B)
            ex,ey=xj-xi,yj-yi
            rx,ry=dx-ex,dy-ey
            err=float(np.hypot(rx,ry))
            flag="OK" if err<=4 else "BAD"
            if err>4: bad.append((fi,fj,round(err,1),round(r,2)))
            print(f"{fi} <-> {fj}: ov{ow}x{oh} exp=({ex},{ey}) meas=({dx:.1f},{dy:.1f}) resid={err:.1f} r={r:.2f} {flag}")
out=os.path.join(ROOT,"out","overlay","v6_stitched_base.png")
cv2.imencode(".png",canvas)[1].tofile(out)
print("BAD>",bad)
print("canvas",canvas.shape)
json.dump({"bad":bad},open(os.path.join(BLK,"custom_report.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
