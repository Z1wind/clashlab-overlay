# -*- coding: utf-8 -*-
"""v0.2.4 QA：标定后收起布局、展开面板、选类型自动收起、放置、导出。"""
import json, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ADB = r"E:\leidian\LDPlayer9\adb.exe"; DEV = "emulator-5554"; QA=os.path.join(BASE,"out","apk_qa")
def sh(*a, timeout=60): return subprocess.run(list(a), capture_output=True, text=True, timeout=timeout)
def tap(x,y,w=0.55): sh(ADB,"-s",DEV,"shell","input","tap",str(int(x)),str(int(y))); time.sleep(w)
def cap(tag):
    p="/sdcard/g_%s.png"%tag; sh(ADB,"-s",DEV,"shell","screencap","-p",p)
    dst=os.path.join(QA,"g2_%s.png"%tag)
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
# 四角（图像区域 y≈240..800）
for p in [(575,520),(960,265),(1345,520),(960,790)]: tap(p[0],p[1],0.5)
img,ts=cap("calib")
print("steps hidden:", not any("点四角" in t for _b,t in ts))
print("palbar:", [t for _b,t in ts if "建筑" in t][:1], "| texts:", [t for _b,t in ts][:10])
h=find(ts,"建筑：")
if h:
    tap(h[0],h[1],0.8)
img,ts=cap("sheet")
print("sheet open:", any("防御" in t for _b,t in ts))
h=find(ts,"散炮")
print("散炮:",h)
if h:
    tap(h[0],h[1],0.8)
img,ts=cap("selected")
print("after select:", [t for _b,t in ts if "建筑" in t or "已选中" in t][:2])
# 放两栋
tap(900,470,0.8); tap(1020,500,0.8)
img,ts=cap("placed")
print("count:", [t for _b,t in ts if "已标" in t][:1])
# 导出
h=find(ts,"导出本张")
if h: tap(h[0],h[1],2.0)
out=os.path.join(QA,"g2_export.json")
if os.path.exists(out): os.remove(out)
for src in ("/sdcard/Download/annot_b01.json",
            "/sdcard/Android/data/com.clashlab.annotator/files/Downloads/annot_b01.json"):
    if os.path.exists(out): os.remove(out)
    sh(ADB,"-s",DEV,"pull",src,out)
    if os.path.exists(out):
        d=json.load(open(out,encoding="utf-8"))
        if d.get("version")==2 and d.get("buildings"):
            print("EXPORT OK:",[(b.get("name"),b.get("tile")) for b in d.get("buildings")])
            break
