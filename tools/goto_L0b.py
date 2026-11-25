# -*- coding: utf-8 -*-
# 强 pinch-in 多轮，每轮存帧并报 MAD，直到画面变成全村视野（人工/后续判）
import subprocess, time, os, cv2, numpy as np
ADB=r"E:\leidian\LDPlayer9\adb.exe"
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
def sh(a,binary=False):
    cp=subprocess.run([ADB]+a,capture_output=True,timeout=30)
    return cp.stdout if binary else cp.stdout.decode("utf-8","ignore")
def frame():
    raw=sh(["exec-out","screencap","-p"],binary=True)
    return cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_COLOR)
prev=frame()
for rnd in range(20):
    sh(["shell","sh","/data/local/tmp/pinchin.sh","20","14"]); time.sleep(1.8)
    cur=frame()
    m=float(np.mean(np.abs(cv2.cvtColor(cur,cv2.COLOR_BGR2GRAY).astype(np.float32)-cv2.cvtColor(prev,cv2.COLOR_BGR2GRAY).astype(np.float32))))
    cv2.imencode(".png",cur)[1].tofile(os.path.join(ROOT,"out","overlay",f"pinch_{rnd:02d}.png"))
    print(f"round{rnd} MAD={m:.1f}")
    prev=cur
