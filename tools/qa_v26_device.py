# -*- coding: utf-8 -*-
"""v0.2.6 真机 QA：四角拖出图片边界 + 导出 corners_norm。"""
import json, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ADB = r"E:\leidian\LDPlayer9\adb.exe"; DEV = "emulator-5554"; QA=os.path.join(BASE,"out","apk_qa")
def sh(*a, timeout=60):
    try: return subprocess.run(list(a), capture_output=True, text=True, timeout=timeout)
    except Exception as e: return None
def tap(x,y,w=0.5): sh(ADB,"-s",DEV,"shell","input","tap",str(int(x)),str(int(y))); time.sleep(w)
def swipe(x1,y1,x2,y2,ms=700): sh(ADB,"-s",DEV,"shell","input","swipe",str(int(x1)),str(int(y1)),str(int(x2)),str(int(y2)),str(ms)); time.sleep(1.3)
def cap(tag):
    p="/sdcard/n_%s.png"%tag; sh(ADB,"-s",DEV,"shell","screencap","-p",p)
    dst=os.path.join(QA,"n_%s.png"%tag)
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
print(sh(ADB,"-s",DEV,"shell","wm","size","1920x864").stdout.strip())
time.sleep(1)
print(sh(ADB,"-s",DEV,"install","-r",r"E:\ClashLab\android\dist\ClashLabAnnotator_v26.apk").stdout.strip())
sh(ADB,"-s",DEV,"shell","pm","clear","com.clashlab.annotator")
sh(ADB,"-s",DEV,"shell","pm","grant","com.clashlab.annotator","android.permission.WRITE_EXTERNAL_STORAGE")
sh(ADB,"-s",DEV,"shell","am","start","-n","com.clashlab.annotator/.MainActivity")
time.sleep(5)
img,ts=cap("a")
h=find(ts,"知道了")
if h: tap(h[0],h[1],1.0)
time.sleep(1)
img,ts=cap("b")
print("page texts:", [t for _b,t in ts][:6])
# 找图片区域：用亮度差异在 stage 内找内容列/行（近似）
gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
cols=gray[220:800,:].mean(axis=0); rows=gray[:,200:1700].mean(axis=1)
xs=[i for i,v in enumerate(cols) if v>25]; ys=[i+220 for i,v in enumerate(rows[220:800]) if v>25]
if xs and ys:
    x0,x1,xm=min(xs),max(xs),(min(xs)+max(xs))//2
    y0,y1,ym=min(ys),max(ys),(min(ys)+max(ys))//2
    print("image bbox approx:", x0,x1,y0,y1)
else:
    x0,x1,y0,y1,xm,ym=400,1520,300,700,(400+1520)//2,500
    print("fallback bbox")
# 点 4 个角（在图片内，任意位置）
for pt in ((x0+60,y0+80),(x1-60,y0+80),(x1-60,y1-80),(x0+60,y1-80)):
    tap(pt[0],pt[1],0.5)
img,ts=cap("c")
hsv=cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
mask=cv2.inRange(hsv,(18,120,160),(40,255,255))
n,lab,stats,cents=cv2.connectedComponentsWithStats(mask,8)
pts=[tuple(map(int,cents[i])) for i in range(1,n) if 40<=stats[i][4]<=2500]
print("yellow markers:", pts[:6])
ok=False
if pts:
    # 拖第 1 个角到图片左侧黑边（图外）
    x0p,y0p=pts[0]
    tx=max(5, x0-200)
    swipe(x0p,y0p,tx,int(y0p),800)
    img,ts=cap("d")
    # 导出
    h=find(ts,"导出本张")
    print("export btn:",h)
    if h:
        tap(h[0],h[1],2.0)
        out=os.path.join(QA,"n_export.json")
        if os.path.exists(out): os.remove(out)
        for src in ("/sdcard/Download/annot_b01.json","/sdcard/Android/data/com.clashlab.annotator/files/Downloads/annot_b01.json"):
            if os.path.exists(out): os.remove(out)
            sh(ADB,"-s",DEV,"pull",src,out)
            if os.path.exists(out):
                d=json.load(open(out,encoding="utf-8"))
                if d.get("version")==2:
                    cn=d.get("corners_norm") or []
                    print("corners_norm:", [[round(v,3) for v in p] for p in cn])
                    print("HAS_OUTSIDE:", any((p[0]<0 or p[0]>1 or p[1]<0 or p[1]>1) for p in cn))
                    ok=True
                    break
print("RESULT ok:", ok)
