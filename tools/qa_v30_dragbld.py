# -*- coding: utf-8 -*-
"""v0.3.0 真机：放建筑 → 拖动 → 导出验证 tile 变化。"""
import json, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ADB = r"E:\leidian\LDPlayer9\adb.exe"; DEV = "emulator-5554"; QA=os.path.join(BASE,"out","apk_qa")
def sh(*a, timeout=60):
    try: return subprocess.run(list(a), capture_output=True, text=True, timeout=timeout)
    except Exception: return None
def tap(x,y,w=0.6): sh(ADB,"-s",DEV,"shell","input","tap",str(int(x)),str(int(y))); time.sleep(w)
def swipe(x1,y1,x2,y2,ms=700): sh(ADB,"-s",DEV,"shell","input","swipe",str(int(x1)),str(int(y1)),str(int(x2)),str(int(y2)),str(ms)); time.sleep(1.5)
def cap(tag):
    p="/sdcard/y_%s.png"%tag; sh(ADB,"-s",DEV,"shell","screencap","-p",p)
    dst=os.path.join(QA,"y2_%s.png"%tag)
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
sh(ADB,"-s",DEV,"shell","wm","size","1920x864"); time.sleep(1.2)
print(sh(ADB,"-s",DEV,"install","-r",r"E:\ClashLab\android\dist\ClashLabAnnotator_v30.apk").stdout.strip())
sh(ADB,"-s",DEV,"shell","pm","clear","com.clashlab.annotator")
sh(ADB,"-s",DEV,"shell","pm","grant","com.clashlab.annotator","android.permission.WRITE_EXTERNAL_STORAGE")
sh(ADB,"-s",DEV,"shell","am","start","-n","com.clashlab.annotator/.MainActivity")
time.sleep(6)
img,ts=cap("a")
if any("知道了" in t for _b,t in ts):
    h=find(ts,"知道了")
    if h: tap(h[0],h[1],1.2)
for pt in ((450,300),(1460,300),(1460,720),(450,720)):
    tap(pt[0],pt[1],0.55)
img,ts=cap("b")
print("pal:", find(ts,"建筑"))
h=find(ts,"建筑")
if h:
    tap(h[0],h[1],0.7)
    img,ts=cap("pal")
    h2=find(ts,"防空")
    print("防空:", h2)
    if h2: tap(h2[0],h2[1],0.7)
tap(900,500,1.0)
img,ts=cap("c")
print("count:", [t for _b,t in ts if "已标" in t][:1])
# 拖动建筑 200px 右
swipe(900,500,1100,500,700)
img,ts=cap("d")
sh(ADB,"-s",DEV,"shell","rm","-f","/sdcard/Download/annot_b01.json")
sh(ADB,"-s",DEV,"shell","rm","-f","/sdcard/Android/data/com.clashlab.annotator/files/Downloads/annot_b01.json")
h=find(ts,"导出本张")
if h: tap(h[0],h[1],2.5)
out=os.path.join(QA,"y2_export.json")
for src in ("/sdcard/Download/annot_b01.json","/sdcard/Android/data/com.clashlab.annotator/files/Downloads/annot_b01.json"):
    if os.path.exists(out): os.remove(out)
    sh(ADB,"-s",DEV,"pull",src,out)
    if os.path.exists(out):
        d=json.load(open(out,encoding="utf-8"))
        print("buildings:", [(b.get("name"),b.get("tile")) for b in d.get("buildings") or []])
        break
sh(ADB,"-s",DEV,"shell","wm","size","1920x1080")
