# -*- coding: utf-8 -*-
# L1 手工链采集：E,S,W,S,E 各步 ORB 测位移+门控，存 blocks_L1，独立偏移表
import subprocess, time, os, json, cv2, numpy as np
ADB=r"E:\leidian\LDPlayer9\adb.exe"
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT=os.path.join(ROOT,"out","overlay","blocks_L1")
os.makedirs(OUT,exist_ok=True)
CROP=(155,80,1105,630)
def sh(a,binary=False):
    cp=subprocess.run([ADB]+a,capture_output=True,timeout=30)
    return cp.stdout if binary else cp.stdout.decode("utf-8","ignore")
def frame():
    raw=sh(["exec-out","screencap","-p"],binary=True)
    return cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_COLOR)
def crop(im): return im[CROP[1]:CROP[3],CROP[0]:CROP[2]]
det=cv2.ORB_create(1500)
def orb(a,b):
    ka,da=det.detectAndCompute(cv2.cvtColor(a,cv2.COLOR_BGR2GRAY),None)
    kb,db=det.detectAndCompute(cv2.cvtColor(b,cv2.COLOR_BGR2GRAY),None)
    if da is None or db is None: return None,0
    bf=cv2.BFMatcher(cv2.NORM_HAMMING)
    good=[m for m,n in bf.knnMatch(da,db,k=2) if m.distance<0.75*n.distance]
    if len(good)<10: return None,len(good)
    pa=np.float32([ka[m.queryIdx].pt for m in good]); pb=np.float32([kb[m.trainIdx].pt for m in good])
    d=pb-pa; mx,my=np.median(d,axis=0)
    inl=np.linalg.norm(d-[mx,my],axis=1)<12
    return (float(mx),float(my)),int(inl.sum())
DRAG={"E":("900","220","180","220"),"W":("380","220","1020","220"),
      "N":("640","40","640","520"),"S":("640","420","640","60")}
seq=["E","S","W","S","E"]
log=[]
prev=crop(frame())
cv2.imencode(".png",prev)[1].tofile(os.path.join(OUT,"l1_00.png"))
log.append({"file":"l1_00.png","dx":0,"dy":0,"inl":99})
acc=[0.0,0.0]
for i,d in enumerate(seq):
    x0,y0,x1,y1=DRAG[d]
    for att in range(3):
        sh(["shell","sh","/data/local/tmp/drag.sh",x0,y0,x1,y1,"24"]); time.sleep(1.5)
        cur=crop(frame()); s,n=orb(prev,cur)
        print(f"{d} att{att} shift={s} inl={n}")
        if s and n>=20: break
    if not s or n<20:
        print("FAIL abort"); break
    acc[0]+=s[0]; acc[1]+=s[1]
    fn=f"l1_{i+1:02d}.png"
    cv2.imencode(".png",cur)[1].tofile(os.path.join(OUT,fn))
    log.append({"file":fn,"dx":round(s[0],1),"dy":round(s[1],1),"inl":n,"acc":[round(acc[0],1),round(acc[1],1)]})
    prev=cur
json.dump(log,open(os.path.join(OUT,"l1_log.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("saved",len(log))
