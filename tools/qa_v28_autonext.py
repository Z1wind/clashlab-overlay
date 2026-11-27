# -*- coding: utf-8 -*-
"""v0.2.8 真机验证：导出后自动跳下一张未标定图。"""
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ADB = r"E:\leidian\LDPlayer9\adb.exe"; DEV = "emulator-5554"; QA=os.path.join(BASE,"out","apk_qa")
def sh(*a, timeout=60):
    try: return subprocess.run(list(a), capture_output=True, text=True, timeout=timeout)
    except Exception: return None
def tap(x,y,w=0.6): sh(ADB,"-s",DEV,"shell","input","tap",str(int(x)),str(int(y))); time.sleep(w)
def cap(tag):
    p="/sdcard/w_%s.png"%tag; sh(ADB,"-s",DEV,"shell","screencap","-p",p)
    dst=os.path.join(QA,"w_%s.png"%tag)
    for _ in range(4):
        sh(ADB,"-s",DEV,"pull",p,dst)
        if os.path.exists(dst): break
        time.sleep(0.4)
    img=cv2.imdecode(np.fromfile(dst,np.uint8),cv2.IMREAD_COLOR)
    E=RapidOCR(); res,_=E(img)
    return img,[(b,str(t)) for b,t,_s in (res or [])]
def find(ts,key):
    for b,t in ts:
        if key in t:
            xs=[p[0] for p in b]; ys=[p[1] for p in b]
            return int(sum(xs)/4),int(sum(ys)/4)
    return None
img,ts=cap("a")
if any("知道了" in t for _b,t in ts):
    h=find(ts,"知道了")
    if h: tap(h[0],h[1],1.2)
    img,ts=cap("a2")
print("tip:", [t for _b,t in ts if "/20" in t][:1])
for pt in ((450,300),(1460,300),(1460,720),(450,720)):
    tap(pt[0],pt[1],0.55)
img,ts=cap("b")
print("hint:", [t for _b,t in ts if "已点" in t][:1])
h=find(ts,"导出本张")
print("export:",h)
if h:
    tap(h[0],h[1],3.0)
img,ts=cap("c")
print("tip after export:", [t for _b,t in ts if "/20" in t][:1])
print("toast:", [t for _b,t in ts if "跳到" in t or "保存" in t][:2])
sh(ADB,"-s",DEV,"shell","wm","size","1920x1080")
