# -*- coding: utf-8 -*-
# 连续 pinch-in 直到与 ladder/zoom_L0.png ORB 高匹配（L0 到顶=无法再缩）
import subprocess, time, os, cv2, numpy as np
ADB=r"E:\leidian\LDPlayer9\adb.exe"
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
def sh(a,binary=False):
    cp=subprocess.run([ADB]+a,capture_output=True,timeout=30)
    return cp.stdout if binary else cp.stdout.decode("utf-8","ignore")
def frame():
    raw=sh(["exec-out","screencap","-p"],binary=True)
    return cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_COLOR)
ref=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","ladder","zoom_L0.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
orb=cv2.ORB_create(1500)
def inliers(a,b):
    ka,da=orb.detectAndCompute(cv2.cvtColor(a,cv2.COLOR_BGR2GRAY),None)
    kb,db=orb.detectAndCompute(cv2.cvtColor(b,cv2.COLOR_BGR2GRAY),None)
    if da is None or db is None: return 0,None
    bf=cv2.BFMatcher(cv2.NORM_HAMMING)
    good=[m for m,n in bf.knnMatch(da,db,k=2) if m.distance<0.75*n.distance]
    if len(good)<10: return len(good),None
    pa=np.float32([ka[m.queryIdx].pt for m in good]); pb=np.float32([kb[m.trainIdx].pt for m in good])
    d=pb-pa; mx,my=np.median(d,axis=0)
    inl=np.linalg.norm(d-[mx,my],axis=1)<15
    return int(inl.sum()),(float(mx),float(my))
prev=frame(); plateau=0
for rnd in range(12):
    sh(["shell","sh","/data/local/tmp/pinch_in.sh","16","12"]); time.sleep(1.8)
    cur=frame()
    m=float(np.mean(np.abs(cv2.cvtColor(cur,cv2.COLOR_BGR2GRAY).astype(np.float32)-cv2.cvtColor(prev,cv2.COLOR_BGR2GRAY).astype(np.float32))))
    n,shift=inliers(cur,ref)
    print(f"round{rnd} MAD={m:.1f} orb_vs_L0={n} shift={shift}")
    cv2.imencode(".png",cur)[1].tofile(os.path.join(ROOT,"out","overlay","goto_L0.png"))
    if n>=250:
        print("REACHED_L0"); break
    plateau=plateau+1 if m<0.8 else 0
    if plateau>=3:
        print("PLATEAU at",n,"inliers"); break
    prev=cur
