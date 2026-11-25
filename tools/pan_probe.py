# -*- coding: utf-8 -*-
# 四向探测：N/W/E/S 各拖250，ORB测位移，找出可动方向
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
def crop(im): return im[CROP[1]:CROP[3],CROP[0]:CROP[2]]
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
# drag.sh: S=(640,420)->(640,170); N=(640,40)->(640,290); E=(900,220)->(650,220); W=(380,220)->(630,220)
moves={"N":("640","40","640","290"),"S":("640","420","640","170"),
       "E":("900","220","650","220"),"W":("380","220","630","220")}
base=frame()
for d,(x0,y0,x1,y1) in moves.items():
    sh(["shell","sh","/data/local/tmp/drag.sh",x0,y0,x1,y1,"20"]); time.sleep(1.4)
    f=frame(); s,n=shift(crop(base),crop(f))
    print(d,"shift=",s,"inl=",n)
    base=f
