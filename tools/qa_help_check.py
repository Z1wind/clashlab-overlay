# -*- coding: utf-8 -*-
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ADB = r"E:\leidian\LDPlayer9\adb.exe"; DEV = "emulator-5554"
QA = os.path.join(BASE, "out", "apk_qa")
def sh(*a, timeout=60): return subprocess.run(list(a), capture_output=True, text=True, timeout=timeout)
def cap(tag):
    p="/sdcard/x.png"; sh(ADB,"-s",DEV,"shell","screencap","-p",p)
    dst=os.path.join(QA, tag+".png"); sh(ADB,"-s",DEV,"pull",p,dst)
    img=cv2.imdecode(np.fromfile(dst,np.uint8),cv2.IMREAD_COLOR)
    E=RapidOCR(); res,_=E(img)
    return img, [(b,str(t)) for b,t,_s in (res or [])]
img, ts = cap("state_now")
print("texts:", [t for _b,t in ts][:14])
# 点帮助
hit=None
for b,t in ts:
    if "怎么用" in t:
        xs=[p[0] for p in b]; ys=[p[1] for p in b]
        hit=(int(sum(xs)/4), int(sum(ys)/4)); break
print("help btn:", hit)
if hit:
    sh(ADB,"-s",DEV,"shell","input","tap",str(hit[0]),str(hit[1]))
    time.sleep(1.5)
    img2, ts2 = cap("help_state")
    print("after help texts:", [t for _b,t in ts2][:12])
    print("has 30秒:", any("30" in t for _b,t in ts2), "| has 第1步:", any("第 1 步" in t or "第1步" in t for _b,t in ts2))
