# -*- coding: utf-8 -*-
"""v0.2.6(最终) 真机 QA：关帮助/ANR → 四角 → 拖出图片 → 导出验证 corners_norm 负值。"""
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
    p="/sdcard/q_%s.png"%tag; sh(ADB,"-s",DEV,"shell","screencap","-p",p)
    dst=os.path.join(QA,"q_%s.png"%tag)
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
print(sh(ADB,"-s",DEV,"install","-r",r"E:\ClashLab\android\dist\ClashLabAnnotator_v26.apk").stdout.strip())
sh(ADB,"-s",DEV,"shell","pm","clear","com.clashlab.annotator")
sh(ADB,"-s",DEV,"shell","pm","grant","com.clashlab.annotator","android.permission.WRITE_EXTERNAL_STORAGE")
sh(ADB,"-s",DEV,"shell","am","start","-n","com.clashlab.annotator/.MainActivity")
time.sleep(6)
for attempt in range(4):
    img,ts=cap("step%d"%attempt)
    txt=[t for _b,t in ts]
    if any("没有响应" in t for t in txt):
        h=find(ts,"等待")
        if h: tap(h[0],h[1],1.5)
        continue
    if any("知道了" in t for t in txt):
        h=find(ts,"知道了")
        if h: tap(h[0],h[1],1.2)
        continue
    break
img,ts=cap("ready")
print("ready texts:", [t for _b,t in ts][:6])
print("help gone:", not any("30秒上手" in t for _b,t in ts))
gray=cv2.cvtColor(img[200:820,:],cv2.COLOR_BGR2GRAY)
cols=gray.mean(axis=0); rows=gray.mean(axis=1)
xs=[i for i,v in enumerate(cols) if v>18]; ys=[i+200 for i,v in enumerate(rows) if v>18]
x0,x1,y0,y1=min(xs),max(xs),min(ys),max(ys)
print("image bbox:", x0,x1,y0,y1)
for pt in ((x0+40,y0+50),(x1-40,y0+50),(x1-40,y1-50),(x0+40,y1-50)):
    tap(pt[0],pt[1],0.55)
img,ts=cap("corners")
hsv=cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
mask=cv2.inRange(hsv,(18,110,150),(42,255,255))
n,lab,stats,cents=cv2.connectedComponentsWithStats(mask,8)
pts=[tuple(map(int,cents[i])) for i in range(1,n) if 40<=stats[i][4]<=3000]
print("yellow markers:", pts[:8])
ok=False
if pts:
    cx,cy=pts[0]
    swipe(cx,cy,max(5,x0-400),cy,900)
    img,ts=cap("dragged")
    h=find(ts,"导出本张")
    if h:
        tap(h[0],h[1],2.5)
        out=os.path.join(QA,"q_export.json")
        for src in ("/sdcard/Download/annot_b01.json","/sdcard/Android/data/com.clashlab.annotator/files/Downloads/annot_b01.json"):
            if os.path.exists(out): os.remove(out)
            sh(ADB,"-s",DEV,"pull",src,out)
            if os.path.exists(out):
                d=json.load(open(out,encoding="utf-8"))
                cn=d.get("corners_norm") or []
                print("version:", d.get("version"), "| corners_norm:", [[round(v,3) for v in p] for p in cn])
                print("HAS_OUTSIDE:", any((p[0]<0 or p[0]>1 or p[1]<0 or p[1]>1) for p in cn))
                ok=True
                break
print("RESULT:", ok)
