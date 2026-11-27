# -*- coding: utf-8 -*-
"""v0.2.5 QA：沿用四角、双击缩放、全清空。"""
import json, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ADB = r"E:\leidian\LDPlayer9\adb.exe"; DEV = "emulator-5554"; QA = os.path.join(BASE,"out","apk_qa")
def sh(*a, timeout=60): return subprocess.run(list(a), capture_output=True, text=True, timeout=timeout)
def tap(x,y,w=0.5): sh(ADB,"-s",DEV,"shell","input","tap",str(int(x)),str(int(y))); time.sleep(w)
def cap(tag):
    p="/sdcard/h_%s.png"%tag; sh(ADB,"-s",DEV,"shell","screencap","-p",p)
    dst=os.path.join(QA,"h_%s.png"%tag)
    for _ in range(3):
        sh(ADB,"-s",DEV,"pull",p,dst)
        if os.path.exists(dst): break
        time.sleep(0.3)
    img=cv2.imdecode(np.fromfile(dst,np.uint8),cv2.IMREAD_COLOR)
    E=RapidOCR(); res,_=E(img)
    return img,[(b,str(t)) for b,t,_s in (res or [])]
def find(ts,key):
    for b,t in ts:
        if key in t:
            xs=[p[0] for p in b]; ys=[p[1] for p in b]
            return int(sum(xs)/4),int(sum(ys)/4)
    return None
print(sh(ADB,"-s",DEV,"install","-r",r"E:\ClashLab\android\dist\ClashLabAnnotator_v25.apk").stdout.strip())
sh(ADB,"-s",DEV,"shell","pm","clear","com.clashlab.annotator")
sh(ADB,"-s",DEV,"shell","pm","grant","com.clashlab.annotator","android.permission.WRITE_EXTERNAL_STORAGE")
sh(ADB,"-s",DEV,"shell","am","start","-n","com.clashlab.annotator/.MainActivity")
time.sleep(3)
img,ts=cap("a")
h=find(ts,"知道了")
if h: tap(h[0],h[1],0.8)
# 第1张标定 + 放一栋
for p in [(575,520),(960,265),(1345,520),(960,790)]: tap(p[0],p[1],0.45)
img,ts=cap("b")
print("p1 calib:", any("已点" not in t for _b,t in ts))
h=find(ts,"建筑")
if h: tap(h[0],h[1],0.6)
img,ts=cap("pal")
h=find(ts,"防空")
if h: tap(h[0],h[1],0.5)
tap(900,470,0.8)
# 下一张 → 沿用四角
h=find(ts,"下一张")
if h: tap(h[0],h[1],0.9)
img,ts=cap("p2")
h=find(ts,"沿上张四角")
print("copy corners btn:", h)
if h: tap(h[0],h[1],0.9)
img,ts=cap("p2c")
print("p2 texts:", [t for _b,t in ts][:8])
# 双击缩放：两次快速点击画布
tap(960,500,0.05); tap(960,500,0.9)
img,ts=cap("zoom")
# 全清空（双段）
h=find(ts,"全清空")
print("clearall:", h)
if h:
    tap(h[0],h[1],0.6); tap(h[0],h[1],0.9)
img,ts=cap("cleared")
print("after clearall:", [t for _b,t in ts if "已标" in t][:1])
