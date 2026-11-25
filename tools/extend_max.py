# -*- coding: utf-8 -*-
# 续跑 pinch-out 到 MAD=0，存 L8/L9...，报每批 MAD
import subprocess, time, os, cv2, numpy as np
ADB=r"E:\leidian\LDPlayer9\adb.exe"; OUT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\ladder"
def sh(a,binary=False):
    cp=subprocess.run([ADB]+a,capture_output=True,timeout=30)
    return cp.stdout if binary else cp.stdout.decode("utf-8","ignore")
def frame():
    raw=sh(["exec-out","screencap","-p"],binary=True)
    return cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_COLOR)
def mad(a,b):
    return float(np.mean(np.abs(cv2.cvtColor(a,cv2.COLOR_BGR2GRAY).astype(np.float32)-cv2.cvtColor(b,cv2.COLOR_BGR2GRAY).astype(np.float32))))
prev=frame(); n=7; plateau=0
while n<14 and plateau<2:
    n+=1
    sh(["shell","sh","/data/local/tmp/pinch.sh","14","10"]); time.sleep(1.6)
    cur=frame(); m=mad(prev,cur)
    cv2.imencode(".png",cur)[1].tofile(os.path.join(OUT,f"zoom_L{n}.png"))
    print(f"L{n} MAD={m:.2f}")
    plateau = plateau+1 if m<1.2 else 0
    prev=cur
print("done, plateau=",plateau)
