# -*- coding: utf-8 -*-
# place.py — 新采集链直接放置；连续链 ORB 复验；输出整阵+编号标注
import json, os, cv2, numpy as np
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BLK=os.path.join(ROOT,"out","overlay","blocks3")
det=cv2.ORB_create(1500)
log=json.load(open(os.path.join(BLK,"collect_log.json"),encoding="utf-8"))
items=[]; cx=cy=0.0
for t in log["tiles"]:
    im=cv2.imdecode(np.fromfile(os.path.join(BLK,t["file"]),dtype=np.uint8),cv2.IMREAD_COLOR)
    im=im[:, :905]  # 已裁顶/左/底；再去右导轨+按钮(设备x1060以右)
    cx+=t["dx"]; cy+=t["dy"]
    items.append((t["file"],im,cx,cy))
minx=min(i[2] for i in items); miny=min(i[3] for i in items)
H,W=items[0][1].shape[:2]
maxx=int(np.ceil(max(i[2]-minx+W for i in items)))
maxy=int(np.ceil(max(i[3]-miny+H for i in items)))
canvas=np.zeros((maxy,maxx,3),np.uint8)
marks=np.zeros((maxy,maxx,3),np.uint8)
pos=[]
for k,(f,im,tx,ty) in enumerate(items):
    x=int(round(tx-minx)); y=int(round(ty-miny))
    canvas[y:y+H,x:x+W]=im
    pos.append((f,x,y))
marks=canvas.copy()
for k,(f,x,y) in enumerate(pos):
    cv2.putText(marks,f"#{k:02d}",(x+20,y+55),cv2.FONT_HERSHEY_SIMPLEX,1.5,(0,0,255),5)

# 连续链全帧 ORB 复验
def orb(a,b):
    ga=cv2.cvtColor(a,cv2.COLOR_BGR2GRAY); gb=cv2.cvtColor(b,cv2.COLOR_BGR2GRAY)
    ka,da=det.detectAndCompute(ga,None); kb,db=det.detectAndCompute(gb,None)
    bf=cv2.BFMatcher(cv2.NORM_HAMMING)
    knn=bf.knnMatch(da,db,k=2)
    good=[m for m,n in knn if m.distance<0.75*n.distance]
    if len(good)<8: return None,len(good)
    pa=np.float32([ka[m.queryIdx].pt for m in good]); pb=np.float32([kb[m.trainIdx].pt for m in good])
    d=pb-pa; mx,my=np.median(d,axis=0)
    inl=np.linalg.norm(d-[mx,my],axis=1)<12
    if inl.sum()>=6: mx,my=np.median(d[inl],axis=0)
    return (float(mx),float(my)),int(inl.sum())

print("== 连续链复验 ==")
worst=0
SKIP={1,2,3}  # 由画布重建的 row0 三帧不参与链复验
for k in range(1,len(items)):
    if k in SKIP:
        print(f"[skip rebuilt row0] {items[k-1][0]}->{items[k][0]}"); continue
    s,n=orb(items[k-1][1],items[k][1])
    ex=items[k][2]-items[k-1][2]; ey=items[k][3]-items[k-1][3]
    if s is None:
        print(f"{items[k-1][0]}->{items[k][0]}: exp=({ex:.0f},{ey:.0f}) meas=NONE skip n={n}")
        continue
    r=float(np.hypot(s[0]-ex,s[1]-ey))
    worst=max(worst,r)
    print(f"{items[k-1][0]}->{items[k][0]}: exp=({ex:.0f},{ey:.0f}) meas=({s[0]:.0f},{s[1]:.0f}) resid={r:.1f} n={n}")
out=os.path.join(ROOT,"out","overlay","v6_stitched_base.png")
cv2.imencode(".png",canvas)[1].tofile(out)
outm=os.path.join(ROOT,"out","overlay","v6_stitched_marks.png")
cv2.imencode(".png",marks)[1].tofile(outm)
print("worst_resid=",round(worst,1),"canvas",canvas.shape)
