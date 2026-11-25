# -*- coding: utf-8 -*-
# 持续pinchin直到pinch MAD<3（=min zoom到顶），落盘最终帧
import subprocess, time, cv2, numpy as np, os
ADB=r"E:\leidian\LDPlayer9\adb.exe"
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT=os.path.join(ROOT,"out","overlay","l0new")
def sh(a,binary=False):
    cp=subprocess.run([ADB]+a,capture_output=True,timeout=30)
    return cp.stdout if binary else cp.stdout.decode("utf-8","ignore")
def frame():
    raw=sh(["exec-out","screencap","-p"],binary=True)
    return cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_COLOR)
CROP=(155,80,1105,630)
def mad(a,b):
    ga=cv2.cvtColor(a[CROP[1]:CROP[3],CROP[0]:CROP[2]],cv2.COLOR_BGR2GRAY).astype(np.float32)
    gb=cv2.cvtColor(b[CROP[1]:CROP[3],CROP[0]:CROP[2]],cv2.COLOR_BGR2GRAY).astype(np.float32)
    return float(np.mean(np.abs(ga-gb)))
prev=frame(); hit=0
for rnd in range(40):
    sh(["shell","sh","/data/local/tmp/pinchin.sh","16","12"]); time.sleep(1.8)
    cur=frame()
    m=mad(prev,cur)
    print(f"r{rnd} pinch MAD={m:.2f}")
    if m<3.0:
        hit+=1
        if hit>=2:
            print("AT_MIN_ZOOM"); break
    else:
        hit=0
    prev=cur
cv2.imencode(".png",cur)[1].tofile(os.path.join(OUT,"l0_min.png"))
