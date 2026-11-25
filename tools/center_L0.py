# -*- coding: utf-8 -*-
# E/N 步移对 zoom_L0 参考 ORB 收敛到中心
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
ref=crop(cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","ladder","zoom_L0.png"),dtype=np.uint8),cv2.IMREAD_COLOR))
det=cv2.ORB_create(1500)
def score(im):
    ka,da=det.detectAndCompute(cv2.cvtColor(im,cv2.COLOR_BGR2GRAY),None)
    kb,db=det.detectAndCompute(cv2.cvtColor(ref,cv2.COLOR_BGR2GRAY),None)
    if da is None or db is None: return 0,None
    bf=cv2.BFMatcher(cv2.NORM_HAMMING)
    good=[m for m,n in bf.knnMatch(da,db,k=2) if m.distance<0.75*n.distance]
    if len(good)<10: return len(good),None
    pa=np.float32([ka[m.queryIdx].pt for m in good]); pb=np.float32([kb[m.trainIdx].pt for m in good])
    d=pb-pa; mx,my=np.median(d,axis=0)
    inn=np.linalg.norm(d-[mx,my],axis=1)<15
    return int(inn.sum()),(float(mx),float(my))
for rnd in range(10):
    im=crop(frame()); n,s=score(im)
    print(rnd,"inl=",n,"shift=",s)
    if n>=300: print("CENTERED"); break
    # 参考在当前的右/北：shift 正=参考在右 → 拖E(左指)；shift y 负=参考在上 → 拖N
    if s and s[0]<-30:
        sh(["shell","sh","/data/local/tmp/drag.sh","900","220","660","220","20"])
    elif s and s[0]>30:
        sh(["shell","sh","/data/local/tmp/drag.sh","380","220","620","220","20"])
    elif s and s[1]<-30:
        sh(["shell","sh","/data/local/tmp/drag.sh","640","40","640","290","20"])
    elif s and s[1]>30:
        sh(["shell","sh","/data/local/tmp/drag.sh","640","420","640","170","20"])
    time.sleep(1.4)
cv2.imencode(".png",im)[1].tofile(os.path.join(ROOT,"out","overlay","l0_centered.png"))
