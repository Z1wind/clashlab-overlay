# -*- coding: utf-8 -*-
import subprocess, time, os, cv2, numpy as np
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
prev=frame(); plateau=0
for rnd in range(16,40):
    sh(["shell","sh","/data/local/tmp/pinchin.sh","16","12"]); time.sleep(1.8)
    cur=frame()
    pc=prev[CROP[1]:CROP[3],CROP[0]:CROP[2]]; cc=cur[CROP[1]:CROP[3],CROP[0]:CROP[2]]
    m=float(np.mean(np.abs(cv2.cvtColor(cc,cv2.COLOR_BGR2GRAY).astype(np.float32)-cv2.cvtColor(pc,cv2.COLOR_BGR2GRAY).astype(np.float32))))
    cv2.imencode(".png",cur)[1].tofile(os.path.join(OUT,f"pinch_{rnd:02d}.png"))
    print(f"round{rnd} MAD={m:.2f}")
    plateau=plateau+1 if m<1.0 else 0
    if plateau>=2:
        print("PLATEAU reached"); break
    prev=cur
