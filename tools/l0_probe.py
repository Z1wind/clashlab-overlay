# -*- coding: utf-8 -*-
# 探针：无操作MAD vs pinch后MAD，判断是否已到min zoom
import subprocess, time, cv2, numpy as np, os
ADB=r"E:\leidian\LDPlayer9\adb.exe"
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
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
f0=frame(); time.sleep(2); f1=frame()
print("no-op MAD=",round(mad(f0,f1),2))
sh(["shell","sh","/data/local/tmp/pinchin.sh","16","12"]); time.sleep(1.8)
f2=frame()
print("pinch MAD=",round(mad(f1,f2),2))
sh(["shell","sh","/data/local/tmp/pinchin.sh","16","12"]); time.sleep(1.8)
f3=frame()
print("pinch2 MAD=",round(mad(f2,f3),2))
cv2.imencode(".png",f3)[1].tofile(os.path.join(ROOT,"out","overlay","l0new","probe.png"))
