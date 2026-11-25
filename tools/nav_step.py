# -*- coding: utf-8 -*-
# 手动导航：参数 dir n，连拖后存帧
import subprocess, time, os, sys, cv2, numpy as np
ADB=r"E:\leidian\LDPlayer9\adb.exe"
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
CROP=(155,80,1105,630)
def sh(a,binary=False):
    cp=subprocess.run([ADB]+a,capture_output=True,timeout=30)
    return cp.stdout if binary else cp.stdout.decode("utf-8","ignore")
def frame():
    raw=sh(["exec-out","screencap","-p"],binary=True)
    return cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_COLOR)
DRAG={"W":("380","220","620","220"),"E":("900","220","660","220"),
      "N":("640","40","640","290"),"S":("640","420","640","170")}
d=sys.argv[1]; n=int(sys.argv[2])
for _ in range(n):
    sh(["shell","sh","/data/local/tmp/drag.sh",*DRAG[d],"20"]); time.sleep(1.3)
im=frame(); cv2.imencode(".png",im[CROP[1]:CROP[3],CROP[0]:CROP[2]])[1].tofile(os.path.join(ROOT,"out","overlay","nav_now.png"))
print("done",d,n)
