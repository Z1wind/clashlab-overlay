# -*- coding: utf-8 -*-
# pinchin 回 L0，ORB 对 zoom_L0 高匹配停
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
det=cv2.ORB_create(1500)
for rnd in range(12):
    sh(["shell","sh","/data/local/tmp/pinchin.sh","16","12"]); time.sleep(1.6)
    cur=frame()
    ka,da=det.detectAndCompute(cv2.cvtColor(cur,cv2.COLOR_BGR2GRAY),None)
    kb,db=det.detectAndCompute(cv2.cvtColor(ref,cv2.COLOR_BGR2GRAY),None)
    bf=cv2.BFMatcher(cv2.NORM_HAMMING)
    good=[m for m,n in bf.knnMatch(da,db,k=2) if m.distance<0.75*n.distance]
    print(rnd,"good=",len(good))
    cv2.imencode(".png",cur)[1].tofile(os.path.join(ROOT,"out","overlay","back_L0.png"))
    if len(good)>=250: print("L0"); break
