# -*- coding: utf-8 -*-
"""v0.2.3 短屏 QA v2：修正底角坐标后重测。"""
import json, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ADB = r"E:\leidian\LDPlayer9\adb.exe"; DEV = "emulator-5554"; QA = os.path.join(BASE,"out","apk_qa")
def sh(*a, timeout=60): return subprocess.run(list(a), capture_output=True, text=True, timeout=timeout)
def tap(x,y,w=0.6): sh(ADB,"-s",DEV,"shell","input","tap",str(int(x)),str(int(y))); time.sleep(w)
def cap(tag):
    p="/sdcard/z_%s.png"%tag; sh(ADB,"-s",DEV,"shell","screencap","-p",p)
    dst=os.path.join(QA,"z_%s.png"%tag)
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
# 重设四角
img,ts=cap("start")
h=find(ts,"重设四角")
if h: tap(h[0],h[1],0.8)
# 四角（底角改 760）
pts=[(575,525),(955,265),(1345,525),(955,760)]
for p in pts: tap(p[0],p[1],0.55)
img,ts=cap("calib")
print("hint:",[t for _b,t in ts if "已点" in t][:2])
h=find(ts,"防空")
print("防空:",h)
if h:
    tap(h[0],h[1],0.5)
    tap(960,540,0.9)
img,ts=cap("p1")
print("count1:",[t for _b,t in ts if "已标" in t][:2])
h=find(ts,"＋")
if h:
    tap(h[0],h[1],0.6); tap(h[0],h[1],0.6)
img,ts=cap("zoom")
tap(1000,600,0.9)
img,ts=cap("p2")
print("count2:",[t for _b,t in ts if "已标" in t][:2])
h=find(ts,"导出本张")
if h: tap(h[0],h[1],2.0)
out=os.path.join(QA,"z_export.json")
if os.path.exists(out): os.remove(out)
for src in ("/sdcard/Download/annot_b01.json",
            "/sdcard/Android/data/com.clashlab.annotator/files/Downloads/annot_b01.json"):
    sh(ADB,"-s",DEV,"pull",src,out)
    if os.path.exists(out):
        d=json.load(open(out,encoding="utf-8"))
        if d.get("version")==2 and d.get("buildings"):
            print("export ok from",src)
            print("version:",d.get("version"),"| size:",d.get("image_size"),"| ncorners:",len(d.get("corners_norm") or []))
            print("buildings:",[(b.get("name"),b.get("tile")) for b in d.get("buildings") or []])
            break
        else:
            print("stale json:",src,"version",d.get("version"),"bld",len(d.get("buildings") or []))
