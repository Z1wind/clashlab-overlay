# -*- coding: utf-8 -*-
"""v0.2.6 真机 QA 第二步：关帮助→点四角→检测黄点→拖出图片→导出。"""
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
def swipe(x1,y1,x2,y2,ms=800): sh(ADB,"-s",DEV,"shell","input","swipe",str(int(x1)),str(int(y1)),str(int(x2)),str(int(y2)),str(ms)); time.sleep(1.4)
def cap(tag):
    p="/sdcard/p_%s.png"%tag; sh(ADB,"-s",DEV,"shell","screencap","-p",p)
    dst=os.path.join(QA,"p_%s.png"%tag)
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
h=find(ts,"知道了")
print("help btn:",h)
if h:
    tap(h[0],h[1],1.2)
img,ts=cap("b")
print("after close:", [t for _b,t in ts][:8])
print("help gone:", not any("30秒上手" in t for _b,t in ts))
# 图片 bbox：stage 里非黑区域
sub=img[200:800,:]
gray=cv2.cvtColor(sub,cv2.COLOR_BGR2GRAY)
cols=gray.mean(axis=0); rows=gray.mean(axis=1)
xs=[i for i,v in enumerate(cols) if v>18]; ys=[i+200 for i,v in enumerate(rows) if v>18]
print("bbox:", (min(xs),max(xs),min(ys),max(ys)) if xs and ys else None)
x0,x1,y0,y1=min(xs),max(xs),min(ys),max(ys)
for pt in ((x0+40,y0+60),(x1-40,y0+60),(x1-40,y1-60),(x0+40,y1-60)):
    tap(pt[0],pt[1],0.55)
img,ts=cap("c")
hsv=cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
mask=cv2.inRange(hsv,(18,110,150),(42,255,255))
n,lab,stats,cents=cv2.connectedComponentsWithStats(mask,8)
pts=[tuple(map(int,cents[i])) for i in range(1,n) if 40<=stats[i][4]<=2500]
print("yellow markers:", pts[:8])
if pts:
    cx,cy=pts[0]
    tx = max(5, x0-300)
    print("drag", (cx,cy), "->", (tx,cy))
    swipe(cx,cy,tx,cy,900)
    img,ts=cap("d")
    h=find(ts,"导出本张")
    print("export:",h)
    if h:
        tap(h[0],h[1],2.5)
        out=os.path.join(QA,"p_export.json")
        for src in ("/sdcard/Download/annot_b01.json","/sdcard/Android/data/com.clashlab.annotator/files/Downloads/annot_b01.json"):
            if os.path.exists(out): os.remove(out)
            sh(ADB,"-s",DEV,"pull",src,out)
            if os.path.exists(out):
                d=json.load(open(out,encoding="utf-8"))
                cn=d.get("corners_norm") or []
                print("version", d.get("version"), "corners:", [[round(v,3) for v in p] for p in cn])
                print("HAS_OUTSIDE:", any((p[0]<0 or p[0]>1 or p[1]<0 or p[1]>1) for p in cn))
                break
