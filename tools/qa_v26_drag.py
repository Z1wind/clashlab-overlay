# -*- coding: utf-8 -*-
"""精确拖拽验证：已有四角→拖第1角到 x=30→导出看 |u|>0.1。"""
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
def swipe(x1,y1,x2,y2,ms=900): sh(ADB,"-s",DEV,"shell","input","swipe",str(int(x1)),str(int(y1)),str(int(x2)),str(int(y2)),str(ms)); time.sleep(1.6)
def cap(tag):
    p="/sdcard/r_%s.png"%tag; sh(ADB,"-s",DEV,"shell","screencap","-p",p)
    dst=os.path.join(QA,"r_%s.png"%tag)
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
sh(ADB,"-s",DEV,"shell","wm","size","1920x864")
time.sleep(1.5)
sh(ADB,"-s",DEV,"shell","am","start","-n","com.clashlab.annotator/.MainActivity")
time.sleep(4)
img,ts=cap("a")
if any("知道了" in t for _b,t in ts):
    h=find(ts,"知道了"); 
    if h: tap(h[0],h[1],1.0)
    img,ts=cap("a2")
print("page:", [t for _b,t in ts][:6])
# 找角点：黄色圆点（大色块，接近正圆）
hsv=cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
mask=cv2.inRange(hsv,(18,130,170),(40,255,255))
mask=cv2.morphologyEx(mask,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
n,lab,stats,cents=cv2.connectedComponentsWithStats(mask,8)
cands=[]
for i in range(1,n):
    a=stats[i][4]; w0=stats[i][2]; h0=stats[i][3]
    if 120<=a<=2000 and 8<=w0<=60 and 8<=h0<=60 and abs(w0-h0)<=10:
        cands.append((int(cents[i][0]),int(cents[i][1]),int(a)))
print("corner candidates:", cands[:8])
if cands:
    cx,cy,ar=cands[0]
    print("drag from", (cx,cy), "to", (30,cy))
    swipe(cx,cy,30,cy,1000)
    img,ts=cap("b")
    h=find(ts,"导出本张")
    if h:
        tap(h[0],h[1],2.5)
        out=os.path.join(QA,"r_export.json")
        for src in ("/sdcard/Download/annot_b01.json","/sdcard/Android/data/com.clashlab.annotator/files/Downloads/annot_b01.json"):
            if os.path.exists(out): os.remove(out)
            sh(ADB,"-s",DEV,"pull",src,out)
            if os.path.exists(out):
                d=json.load(open(out,encoding="utf-8"))
                cn=d.get("corners_norm") or []
                print("corners_norm:", [[round(v,3) for v in p] for p in cn])
                print("MAX_OUTSIDE:", max(max(-p[0],p[0]-1,-p[1],p[1]-1) for p in cn) if cn else None)
                break
sh(ADB,"-s",DEV,"shell","wm","size","1920x1080")
