# -*- coding: utf-8 -*-
"""v0.2.2 导出目标验证：装新包、清旧文件、标注一次、导出，检查「下载」。"""
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ADB = r"E:\leidian\LDPlayer9\adb.exe"; DEV = "emulator-5554"; QA = os.path.join(BASE,"out","apk_qa")
def sh(*a, timeout=60): return subprocess.run(list(a), capture_output=True, text=True, timeout=timeout)
def tap(x,y,w=0.7): sh(ADB,"-s",DEV,"shell","input","tap",str(int(x)),str(int(y))); time.sleep(w)
def cap(tag):
    p="/sdcard/x_%s.png"%tag; sh(ADB,"-s",DEV,"shell","screencap","-p",p)
    dst=os.path.join(QA,"x_%s.png"%tag)
    for _ in range(3):
        sh(ADB,"-s",DEV,"pull",p,dst)
        if os.path.exists(dst): break
        time.sleep(0.3)
    img=cv2.imdecode(np.fromfile(dst,np.uint8),cv2.IMREAD_COLOR)
    E=RapidOCR(); res,_=E(img)
    return [(b,str(t)) for b,t,_s in (res or [])]
def find(ts,key):
    for b,t in ts:
        if key in t:
            xs=[p[0] for p in b]; ys=[p[1] for p in b]
            return int(sum(xs)/4),int(sum(ys)/4)
    return None
print(sh(ADB,"-s",DEV,"install","-r",r"E:\ClashLab\android\dist\ClashLabAnnotator_v22.apk").stdout.strip())
sh(ADB,"-s",DEV,"shell","rm","-f","/sdcard/Download/annot_b01.json","/sdcard/Download/annot_b02.json","/sdcard/Download/annot_all.json")
sh(ADB,"-s",DEV,"shell","pm","clear","com.clashlab.annotator")
sh(ADB,"-s",DEV,"shell","pm","grant","com.clashlab.annotator","android.permission.WRITE_EXTERNAL_STORAGE")
sh(ADB,"-s",DEV,"shell","am","start","-n","com.clashlab.annotator/.MainActivity")
time.sleep(3)
ts = cap("a")
h=find(ts,"知道了")
if h: tap(h[0],h[1],1.0)
pts=[(600,470),(960,290),(1330,470),(960,630)]
for p in pts: tap(p[0],p[1],0.5)
ts = cap("b")
h=find(ts,"防空")
if h: tap(h[0],h[1],0.5)
tap(960,420,0.8)
ts = cap("c")
print("count:",[t for _b,t in ts if "已标" in t][:2])
h=find(ts,"导出本张")
if h: tap(h[0],h[1],2.0)
ts = cap("d")
print("toast:",[t for _b,t in ts if "保存" in t or "下载" in t or "失败" in t][:3])
print("--- Download ---")
print(sh(ADB,"-s",DEV,"shell","ls","-l","/sdcard/Download").stdout.strip()[:600])
