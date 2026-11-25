# -*- coding: utf-8 -*-
# 抓当前帧 vs 指定前块 ORB 测位移，追加进 l1_log
import subprocess, time, os, json, sys, cv2, numpy as np
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
    bf=cv2.BFMatcher(cv2.NORM_HAMMING)
    good=[m for m,n in bf.knnMatch(da,db,k=2) if m.distance<0.75*n.distance]
    pa=np.float32([ka[m.queryIdx].pt for m in good]); pb=np.float32([kb[m.trainIdx].pt for m in good])
    d=pb-pa; mx,my=np.median(d,axis=0)
    inl=np.linalg.norm(d-[mx,my],axis=1)<12
    return (float(mx),float(my)),int(inl.sum()),len(good)
prev_name=sys.argv[1]; out_name=sys.argv[2]
prev=cv2.imdecode(np.fromfile(os.path.join(OUT,prev_name),dtype=np.uint8),cv2.IMREAD_COLOR)
cur=crop(frame())
s,n,g=orb(prev,cur)
print("shift=",s,"inl=",n,"good=",g)
log=json.load(open(os.path.join(OUT,"l1_log.json"),encoding="utf-8"))
acc=[log[-1]["acc"][0]+s[0],log[-1]["acc"][1]+s[1]]
cv2.imencode(".png",cur)[1].tofile(os.path.join(OUT,out_name))
log.append({"file":out_name,"dx":round(s[0],1),"dy":round(s[1],1),"inl":n,"acc":[round(acc[0],1),round(acc[1],1)]})
json.dump(log,open(os.path.join(OUT,"l1_log.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
