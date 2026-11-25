# -*- coding: utf-8 -*-
# 受控竖扫：N到顶F1；每步S小拖~150px，ORB测步距并落盘帧，直到南锁；多帧链
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
# N到顶
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
f0=frame()
frames=[crop(f0)]
cum=0.0; meta=[{"y":0.0}]
# S小步链
prev=crop(f0); lock=0
for step in range(8):
    sh(["shell","sh","/data/local/tmp/drag.sh","640","430","640","170","18"]); time.sleep(1.8)
    cur=crop(frame())
    (sx,sy),nin,ng=orb_shift(prev,cur)
    print(f"S{step} shift=({sx},{sy}) inl={nin}/{ng}")
    if sy is None or abs(sy)<8:
        lock+=1
        if lock>=2: print("SOUTH LOCKED"); break
    else:
        lock=0; cum+= -sy
        frames.append(cur); meta.append({"y":cum})
    prev=cur
for i,fr in enumerate(frames):
    cv2.imencode(".png",fr)[1].tofile(os.path.join(OUT,f"f{i}.png"))
json.dump(meta,open(os.path.join(OUT,"chain.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("frames=",len(frames),"cum=",cum)
