# -*- coding: utf-8 -*-
"""最终 APK：安装、授权、快速标注、导出，验证落到「下载」。"""
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ADB = r"E:\leidian\LDPlayer9\adb.exe"; DEV = "emulator-5554"
QA = os.path.join(BASE, "out", "apk_qa")
def sh(*a, timeout=90): return subprocess.run(list(a), capture_output=True, text=True, timeout=timeout)
def tap(x,y,w=0.8): sh(ADB,"-s",DEV,"shell","input","tap",str(x),str(y)); time.sleep(w)
def cap(tag):
    p="/sdcard/final_%s.png"%tag; sh(ADB,"-s",DEV,"shell","screencap","-p",p)
    dst=os.path.join(QA,"final_%s.png"%tag)
    for _ in range(3):
        sh(ADB,"-s",DEV,"pull",p,dst)
        if os.path.exists(dst) and os.path.getsize(dst)>1000: break
        time.sleep(0.3)
    img=cv2.imdecode(np.fromfile(dst,np.uint8),cv2.IMREAD_COLOR)
    E=RapidOCR(); res,_=E(img)
    return [(b,str(t)) for b,t,_s in (res or [])]
def find(ts,key):
    for b,t in ts:
        if key in t:
            xs=[p[0] for p in b]; ys=[p[1] for p in b]
            return int(sum(xs)/4), int(sum(ys)/4)
    return None
apk = r"E:\ClashLab\android\dist\ClashLabAnnotator_v20.apk"
print(sh(ADB,"-s",DEV,"install","-r",apk).stdout.strip())
sh(ADB,"-s",DEV,"shell","pm","grant","com.clashlab.annotator","android.permission.WRITE_EXTERNAL_STORAGE")
sh(ADB,"-s",DEV,"shell","am","start","-n","com.clashlab.annotator/.MainActivity")
time.sleep(3)
ts = cap("a")
if find(ts,"知道了"):
    h=find(ts,"知道了"); tap(h[0],h[1],0.8)
tap(600,470,0.4); tap(960,290,0.4); tap(1330,470,0.4); tap(960,630,0.8)
tap(95,760,0.4); tap(960,480,0.7)
ts = cap("b")
print("count:", [t for _b,t in ts if "已标" in t][:2])
h = find(ts,"导出本张")
if h: tap(h[0],h[1],1.8)
ts = cap("c")
print("toast:", [t for _b,t in ts if "保存" in t or "下载" in t][:3])
print("--- Download dir ---")
print(sh(ADB,"-s",DEV,"shell","ls","-l","/sdcard/Download").stdout.strip()[:500])
