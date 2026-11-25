# -*- coding: utf-8 -*-
# 试两种拖法，测位移
import subprocess, time, os, cv2, numpy as np
ADB=r"E:\leidian\LDPlayer9\adb.exe"
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
CROP=(155,80,1105,630)
def sh(a,binary=False):
    cp=subprocess.run([ADB]+a,capture_output=True,timeout=30)
    return cp.stdout if binary else cp.stdout.decode("utf-8","ignore")
def frame():
    raw=sh(["exec-out","screencap","-p"],binary=True)
    return cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_COLOR)
def crop(im):
    return im[CROP[1]:CROP[3],CROP[0]:CROP[2]]
orb=cv2.ORB_create(1500)
def shift(a,b):
    ka,da=orb.detectAndCompute(cv2.cvtColor(a,cv2.COLOR_BGR2GRAY),None)
    kb,db=orb.detectAndCompute(cv2.cvtColor(b,cv2.COLOR_BGR2GRAY),None)
    bf=cv2.BFMatcher(cv2.NORM_HAMMING)
    good=[m for m,n in bf.knnMatch(da,db,k=2) if m.distance<0.75*n.distance]
    if len(good)<10: return None,0
    pa=np.float32([ka[m.queryIdx].pt for m in good]); pb=np.float32([kb[m.trainIdx].pt for m in good])
    d=pb-pa; mx,my=np.median(d,axis=0)
    inl=np.linalg.norm(d-[mx,my],axis=1)<12
    return (float(mx),float(my)),int(inl.sum())
base=frame()
# 法1: input swipe
sh(["shell","input","swipe","640","420","640","180","400"]); time.sleep(1.5)
f1=frame(); s,n=shift(crop(base),crop(f1)); print("input swipe:",s,"inl=",n)
# 法2: drag.sh
sh(["shell","sh","/data/local/tmp/drag.sh","640","420","640","180","24"]); time.sleep(1.5)
f2=frame(); s,n=shift(crop(f1),crop(f2)); print("drag.sh:",s,"inl=",n)
cv2.imencode(".png",f1)[1].tofile(os.path.join(ROOT,"out","overlay","pan1.png"))
cv2.imencode(".png",f2)[1].tofile(os.path.join(ROOT,"out","overlay","pan2.png"))
