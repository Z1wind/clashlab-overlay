# -*- coding: utf-8 -*-
# Step1采集：N到顶抓A -> S拖~390px抓B；ORB测dy；落盘l0new/A.png B.png（裁片+全帧）
import subprocess, time, os, cv2, numpy as np, json
ADB=r"E:\leidian\LDPlayer9\adb.exe"
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT=os.path.join(ROOT,"out","overlay","l0new")
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
for i in range(8):
    sh(["shell","sh","/data/local/tmp/drag.sh","640","40","640","520","24"]); time.sleep(1.6)
    cur=crop(frame())
    (sx,sy),nin,ng=orb_shift(prev,cur)
    print(f"N{i} shift=({sx},{sy}) inl={nin}/{ng}")
    if sx is None or abs(sy)<8: locked+=1
    else: locked=0
    if locked>=2: print("NORTH LOCKED"); break
    prev=cur
A=frame()
cv2.imencode(".png",A)[1].tofile(os.path.join(OUT,"A_full.png"))
cv2.imencode(".png",crop(A))[1].tofile(os.path.join(OUT,"A.png"))
# 2) S拖 ~390px
sh(["shell","sh","/data/local/tmp/drag.sh","640","430","640","40","24"]); time.sleep(1.8)
B=frame(); Bc=crop(B)
(sx,sy),nin,ng=orb_shift(crop(A),Bc)
print(f"S drag shift=({sx},{sy}) inl={nin}/{ng}")
cv2.imencode(".png",B)[1].tofile(os.path.join(OUT,"B_full.png"))
cv2.imencode(".png",Bc)[1].tofile(os.path.join(OUT,"B.png"))
json.dump({"dy_orb":sy,"dx_orb":sx,"inl":nin,"good":ng},open(os.path.join(OUT,"capture.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("saved A/B")
