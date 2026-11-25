# -*- coding: utf-8 -*-
# 续采：N,E 补北行，追加到 blocks_L1
import subprocess, time, os, json, cv2, numpy as np
ADB=r"E:\leidian\LDPlayer9\adb.exe"
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT=os.path.join(ROOT,"out","overlay","blocks_L1")
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
log=json.load(open(os.path.join(OUT,"l1_log.json"),encoding="utf-8"))
prev=crop(frame())
seq=[("N",("640","40","640","520"),"l1_04.png"),("E",("900","220","180","220"),"l1_05.png")]
acc=[log[-1]["acc"][0],log[-1]["acc"][1]]
for d,dr,fn in seq:
    for att in range(3):
        sh(["shell","sh","/data/local/tmp/drag.sh",*dr,"24"]); time.sleep(1.5)
        cur=crop(frame()); s,n=orb(prev,cur)
        print(d,"att",att,s,n)
        if s and n>=20: break
    if not s or n<20: print("FAIL"); break
    acc[0]+=s[0]; acc[1]+=s[1]
    cv2.imencode(".png",cur)[1].tofile(os.path.join(OUT,fn))
    log.append({"file":fn,"dx":round(s[0],1),"dy":round(s[1],1),"inl":n,"acc":[round(acc[0],1),round(acc[1],1)]})
    prev=cur
json.dump(log,open(os.path.join(OUT,"l1_log.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("total",len(log))
