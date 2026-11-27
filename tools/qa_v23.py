# -*- coding: utf-8 -*-
"""v0.2.3 短屏 QA：四角→列表→放大→放置→导出。"""
import json, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ADB = r"E:\leidian\LDPlayer9\adb.exe"; DEV = "emulator-5554"; QA = os.path.join(BASE,"out","apk_qa")
def sh(*a, timeout=60): return subprocess.run(list(a), capture_output=True, text=True, timeout=timeout)
def tap(x,y,w=0.6): sh(ADB,"-s",DEV,"shell","input","tap",str(int(x)),str(int(y))); time.sleep(w)
def cap(tag):
    p="/sdcard/y_%s.png"%tag; sh(ADB,"-s",DEV,"shell","screencap","-p",p)
    dst=os.path.join(QA,"y_%s.png"%tag)
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
pts=[(575,525),(955,265),(1345,525),(955,805)]
for p in pts: tap(p[0],p[1],0.5)
img,ts=cap("calib")
print("hint:",[t for _b,t in ts if "已点" in t][:2])
# 列表出现：找「防空」
h=find(ts,"防空")
print("防空 btn:",h)
if h: tap(h[0],h[1],0.5)
# 放置 1
tap(960,540,0.8)
img,ts=cap("placed1")
print("count1:",[t for _b,t in ts if "已标" in t][:2])
# 放大两次
h=find(ts,"＋") or find(ts,"+")
print("zoom+:",h)
if h:
    tap(h[0],h[1],0.6); tap(h[0],h[1],0.6)
img,ts=cap("zoomed")
# 放大后再放一个（位置不同）
tap(1000,600,0.8)
img,ts=cap("placed2")
print("count2:",[t for _b,t in ts if "已标" in t][:2])
# 适应 + 导出
h=find(ts,"适应")
if h: tap(h[0],h[1],0.6)
h=find(ts,"导出本张")
print("export:",h)
if h: tap(h[0],h[1],2.0)
# 校验导出（先 Downloads 后私有）
out=os.path.join(QA,"y_export.json")
for src in ("/sdcard/Download/annot_b01.json",
            "/sdcard/Android/data/com.clashlab.annotator/files/Downloads/annot_b01.json"):
    sh(ADB,"-s",DEV,"pull",src,out)
    if os.path.exists(out):
        d=json.load(open(out,encoding="utf-8"))
        print("json from",src,"| version:",d.get("version"),"| size:",d.get("image_size"),"| ncorners:",len(d.get("corners_norm") or []),"| bld:",[(b.get("name"),b.get("tile")) for b in d.get("buildings") or []])
        break
