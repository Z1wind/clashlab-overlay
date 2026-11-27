# -*- coding: utf-8 -*-
"""v0.2.5 QA v2：关教程→标定→放置→下一张→沿用四角→双击缩放→全清空。"""
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ADB = r"E:\leidian\LDPlayer9\adb.exe"; DEV = "emulator-5554"; QA=os.path.join(BASE,"out","apk_qa")
def sh(*a, timeout=60): return subprocess.run(list(a), capture_output=True, text=True, timeout=timeout)
def tap(x,y,w=0.5): sh(ADB,"-s",DEV,"shell","input","tap",str(int(x)),str(int(y))); time.sleep(w)
def cap(tag):
    p="/sdcard/k_%s.png"%tag; sh(ADB,"-s",DEV,"shell","screencap","-p",p)
    dst=os.path.join(QA,"k_%s.png"%tag)
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
img,ts=cap("a")
print("top texts:", [t for _b,t in ts][:10])
h=find(ts,"知道了")
if h: tap(h[0],h[1],0.9)
img,ts=cap("b")
print("after help:", [t for _b,t in ts][:10])
# 第1张四角
for p in [(575,520),(960,265),(1345,520),(960,790)]: tap(p[0],p[1],0.45)
img,ts=cap("c")
h=find(ts,"建筑")
print("palbtn:",h)
if h: tap(h[0],h[1],0.6)
img,ts=cap("d")
h=find(ts,"防空")
print("防空:",h)
if h: tap(h[0],h[1],0.5)
tap(900,470,0.8)
img,ts=cap("e")
print("count1:", [t for _b,t in ts if "已标" in t][:1])
# 下一张
h=find(ts,"下一张")
print("next:",h)
if h: tap(h[0],h[1],1.0)
img,ts=cap("f")
print("page2:", [t for _b,t in ts if "/20" in t][:1], "| copy btn:", find(ts,"沿上张"))
h=find(ts,"沿上张")
if h:
    tap(h[0],h[1],0.9)
    img,ts=cap("g")
    print("after copy:", [t for _b,t in ts if "已标" in t or "沿用" in t][:2])
# 双击缩放
tap(960,600,0.05); tap(960,600,0.9)
img,ts=cap("h")
print("zoom toast:", [t for _b,t in ts if "双击" in t or "放大" in t][:2])
# 全清空
h=find(ts,"全清空")
print("clearall btn:",h)
if h:
    tap(h[0],h[1],0.6); tap(h[0],h[1],1.0)
    img,ts=cap("i")
    print("cleared:", [t for _b,t in ts if "已标" in t or "清空" in t][:3])
