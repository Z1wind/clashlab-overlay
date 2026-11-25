# -*- coding: utf-8 -*-
# 抓帧对比 b29：确认设备仍在采集位置、缩放未重置
import subprocess, cv2, numpy as np, os, json
ADB=r"E:\leidian\LDPlayer9\adb.exe"
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BLK=os.path.join(ROOT,"out","overlay","blocks3")
raw=subprocess.run([ADB,"exec-out","screencap","-p"],capture_output=True,timeout=30).stdout
im=cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_COLOR)
CROP=(155,80,1105,630)
cur=im[CROP[1]:CROP[3],CROP[0]:CROP[2]]
ref=cv2.imdecode(np.fromfile(os.path.join(BLK,"b29.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
orb=cv2.ORB_create(1200)
ka,da=orb.detectAndCompute(cv2.cvtColor(cur,cv2.COLOR_BGR2GRAY),None)
kb,db=orb.detectAndCompute(cv2.cvtColor(ref,cv2.COLOR_BGR2GRAY),None)
bf=cv2.BFMatcher(cv2.NORM_HAMMING)
good=[m for m,n in bf.knnMatch(da,db,k=2) if m.distance<0.75*n.distance]
print("matches vs b29:",len(good))
cv2.imencode(".png",cur)[1].tofile(os.path.join(ROOT,"out","overlay","state_now.png"))
