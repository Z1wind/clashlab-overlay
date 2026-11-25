# -*- coding: utf-8 -*-
# 三张竖扫 stage1: N到顶抓S1；S拖~330抓S2；再S拖~330抓S3；ORB测步距落盘
import subprocess, time, os, cv2, numpy as np, json
ADB=r"E:\leidian\LDPlayer9\adb.exe"
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT=os.path.join(ROOT,"out","overlay","l0three"); os.makedirs(OUT,exist_ok=True)
CROP=(155,80,1105,630)
def sh(a,binary=False):
    cp=subprocess.run([ADB]+a,capture_output=True,timeout=30)
    return cp.stdout if binary else cp.stdout.decode("utf-8","ignore")
def frame():
    raw=sh(["exec-out","screencap","-p"],binary=True)
    return cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_COLOR)
def crop(im):
    x1,y1,x2,y2=CROP; return im[y1:y2,x1:x2]
orb=cv2.ORB_create(1500)
def orb_shift(a,b):
    ka,da=orb.detectAndCompute(cv2.cvtColor(a,cv2.COLOR_BGR2GRAY),None)
    kb,db=orb.detectAndCompute(cv2.cvtColor(b,cv2.COLOR_BGR2GRAY),None)
    if da is None or db is None: return None,0,0
    bf=cv2.BFMatcher(cv2.NORM_HAMMING)
    good=[m for m,n in bf.knnMatch(da,db,k=2) if m.distance<0.75*n.distance]
    if len(good)<10: return None,0,len(good)
    pa=np.float32([ka[m.queryIdx].pt for m in good]); pb=np.float32([kb[m.trainIdx].pt for m in good])
    d=pb-pa; mx,my=np.median(d,axis=0)
    inl=np.linalg.norm(d-[mx,my],axis=1)<12
    return (float(mx),float(my)),int(inl.sum()),len(good)
# 1) N到顶
prev=crop(frame()); locked=0
for i in range(10):
    sh(["shell","sh","/data/local/tmp/drag.sh","640","40","640","520","24"]); time.sleep(1.6)
    cur=crop(frame())
    (sx,sy),nin,ng=orb_shift(prev,cur)
    print(f"N{i} shift=({sx},{sy}) inl={nin}/{ng}")
    if sx is None or abs(sy)<8: locked+=1
    else: locked=0
    if locked>=2: print("NORTH LOCKED"); break
    prev=cur
S1=frame()
cv2.imencode(".png",crop(S1))[1].tofile(os.path.join(OUT,"s1.png"))
cv2.imencode(".png",S1)[1].tofile(os.path.join(OUT,"s1_full.png"))
# 2) S拖到S2，目标步距310-350
def s_drag(target, prevc, tag):
    cur=prevc
    total=0.0
    for att in range(4):
        sh(["shell","sh","/data/local/tmp/drag.sh","640","430","640","20","24"]); time.sleep(1.8)
        nxt=crop(frame())
        (sx,sy),nin,ng=orb_shift(cur,nxt)
        print(f"{tag} att{att} shift=({sx},{sy}) inl={nin}/{ng}")
        if sy is None: break
        total+= -sy
        cur=nxt
        if total>=target-20: break
    return cur,total
c2,d2=s_drag(330,crop(S1),"S->S2")
S2=frame()
cv2.imencode(".png",c2)[1].tofile(os.path.join(OUT,"s2.png"))
cv2.imencode(".png",S2)[1].tofile(os.path.join(OUT,"s2_full.png"))
# 3) S拖到S3
c3,d3=s_drag(330,c2,"S->S3")
S3=frame()
cv2.imencode(".png",c3)[1].tofile(os.path.join(OUT,"s3.png"))
cv2.imencode(".png",S3)[1].tofile(os.path.join(OUT,"s3_full.png"))
json.dump({"d2":d2,"d3":d3},open(os.path.join(OUT,"capt.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("saved s1/s2/s3 d2=",d2,"d3=",d3)
