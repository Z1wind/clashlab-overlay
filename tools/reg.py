# -*- coding: utf-8 -*-
# reg.py — ORB 连续帧配准链：相邻块 ORB 匹配中位平移 → 修正累积偏移 → 放置 → 残差报告
import json, os, cv2, numpy as np
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BLK=os.path.join(ROOT,"out","overlay","blocks")
log=json.load(open(os.path.join(BLK,"collect_log.json"),encoding="utf-8"))
files=[t["file"] for t in log["tiles"]]
imgs=[cv2.imdecode(np.fromfile(os.path.join(BLK,f),dtype=np.uint8),cv2.IMREAD_COLOR) for f in files]
orb=cv2.ORB_create(1000)

def match_shift(a,b):
    ga=cv2.cvtColor(a,cv2.COLOR_BGR2GRAY); gb=cv2.cvtColor(b,cv2.COLOR_BGR2GRAY)
    ka,da=orb.detectAndCompute(ga,None); kb,db=orb.detectAndCompute(gb,None)
    if da is None or db is None or len(ka)<10 or len(kb)<10: return None,0
    bf=cv2.BFMatcher(cv2.NORM_HAMMING)
    knn=bf.knnMatch(da,db,k=2)
    good=[m for m,n in knn if m.distance<0.75*n.distance]
    if len(good)<8: return None,len(good)
    pa=np.float32([ka[m.queryIdx].pt for m in good])
    pb=np.float32([kb[m.trainIdx].pt for m in good])
    d=pb-pa
    # RANSAC-ish: 用中位
    mx,my=np.median(d,axis=0)
    inl=np.linalg.norm(d-[mx,my],axis=1)<8
    if inl.sum()>=6:
        mx,my=np.median(d[inl],axis=0)
    return (float(mx),float(my)),int(inl.sum())

offs=[(0.0,0.0)]
print("== ORB 相邻配准 ==")
for i in range(1,len(imgs)):
    s,n=match_shift(imgs[i-1],imgs[i])
    if s is None:
        print(f"{files[i-1]}->{files[i]}: FAIL n={n}"); offs.append(None)
    else:
        px,py=offs[-1]
        offs.append((px+s[0],py+s[1]))
        print(f"{files[i-1]}->{files[i]}: dx={s[0]:.1f} dy={s[1]:.1f} inl={n} cum=({px+s[0]:.0f},{py+s[1]:.0f})")
json.dump({"offs":offs},open(os.path.join(BLK,"orb_offs.json"),"w",encoding="utf-8"))
