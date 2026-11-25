# -*- coding: utf-8 -*-
# 到L0：连续pinchin到顶（MAD连续两次<0.8），ORB对照ladder/zoom_L0；落盘每轮帧
import subprocess, time, os, cv2, numpy as np
ADB=r"E:\leidian\LDPlayer9\adb.exe"
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT=os.path.join(ROOT,"out","overlay","l0new"); os.makedirs(OUT,exist_ok=True)
def sh(a,binary=False):
    cp=subprocess.run([ADB]+a,capture_output=True,timeout=30)
    return cp.stdout if binary else cp.stdout.decode("utf-8","ignore")
def frame():
    raw=sh(["exec-out","screencap","-p"],binary=True)
    return cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_COLOR)
ref=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","ladder","zoom_L0.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
refc=ref[80:630,155:1105]
orb=cv2.ORB_create(1500)
def orb_inl(a,b):
    ka,da=orb.detectAndCompute(cv2.cvtColor(a,cv2.COLOR_BGR2GRAY),None)
    kb,db=orb.detectAndCompute(cv2.cvtColor(b,cv2.COLOR_BGR2GRAY),None)
    if da is None or db is None: return 0,(None,None),0
    bf=cv2.BFMatcher(cv2.NORM_HAMMING)
    good=[m for m,n in bf.knnMatch(da,db,k=2) if m.distance<0.75*n.distance]
    if len(good)<10: return len(good),(None,None),len(good)
    pa=np.float32([ka[m.queryIdx].pt for m in good]); pb=np.float32([kb[m.trainIdx].pt for m in good])
    d=pb-pa; mx,my=np.median(d,axis=0)
    inl=np.linalg.norm(d-[mx,my],axis=1)<15
    return int(inl.sum()),(float(mx),float(my)),len(good)
CROP=(155,80,1105,630)
prev=frame(); plateau=0
for rnd in range(15):
    sh(["shell","sh","/data/local/tmp/pinchin.sh","16","12"]); time.sleep(1.8)
    cur=frame()
    ccc=cur[CROP[1]:CROP[3],CROP[0]:CROP[2]]
    m=float(np.mean(np.abs(cv2.cvtColor(ccc,cv2.COLOR_BGR2GRAY).astype(np.float32)-cv2.cvtColor(prev[CROP[1]:CROP[3],CROP[0]:CROP[2]],cv2.COLOR_BGR2GRAY).astype(np.float32))))
    n,shift,good=orb_inl(ccc,refc)
    cv2.imencode(".png",cur)[1].tofile(os.path.join(OUT,f"pinch_{rnd:02d}.png"))
    print(f"round{rnd} MAD={m:.2f} orb_vs_L0={n} good={good} shift={shift}")
    plateau=plateau+1 if m<0.8 else 0
    if plateau>=2:
        print("PLATEAU reached, n=",n); break
    prev=cur
