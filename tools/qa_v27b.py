# -*- coding: utf-8 -*-
"""v0.2.7 重测：拖角到上边缘，画面不应消失，角点 y 应 < -0.05。"""
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
def swipe(x1,y1,x2,y2,ms=800): sh(ADB,"-s",DEV,"shell","input","swipe",str(int(x1)),str(int(y1)),str(int(x2)),str(int(y2)),str(ms)); time.sleep(1.5)
def cap(tag):
    p="/sdcard/t_%s.png"%tag; sh(ADB,"-s",DEV,"shell","screencap","-p",p)
    dst=os.path.join(QA,"t_%s.png"%tag)
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
print(sh(ADB,"-s",DEV,"shell","wm","size","1920x864").stdout.strip()); time.sleep(1.2)
print(sh(ADB,"-s",DEV,"install","-r",r"E:\ClashLab\android\dist\ClashLabAnnotator_v27.apk").stdout.strip())
sh(ADB,"-s",DEV,"shell","pm","clear","com.clashlab.annotator")
sh(ADB,"-s",DEV,"shell","pm","grant","com.clashlab.annotator","android.permission.WRITE_EXTERNAL_STORAGE")
sh(ADB,"-s",DEV,"shell","am","start","-n","com.clashlab.annotator/.MainActivity")
time.sleep(6)
img,ts=cap("a")
if any("知道了" in t for _b,t in ts):
    h=find(ts,"知道了")
    if h: tap(h[0],h[1],1.2)
    img,ts=cap("a2")
print("page:", [t for _b,t in ts][:6])
gray=cv2.cvtColor(img[190:830,:],cv2.COLOR_BGR2GRAY)
cols=gray.mean(axis=0); rows=gray.mean(axis=1)
xs=[i for i,v in enumerate(cols) if v>18]; ys=[i+190 for i,v in enumerate(rows) if v>18]
x0,x1,y0,y1=min(xs),max(xs),min(ys),max(ys)
print("bbox:", x0,x1,y0,y1)
for pt in ((x0+80,y0+80),(x1-120,y0+80),(x1-120,y1-80),(x0+80,y1-80)):
    tap(pt[0],pt[1],0.5)
img,ts=cap("b")
hsv=cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
mask=cv2.inRange(hsv,(18,130,170),(40,255,255)); mask[:190,:]=0; mask[830:,:]=0
mask=cv2.morphologyEx(mask,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
n,lab,stats,cents=cv2.connectedComponentsWithStats(mask,8)
cands=[]
for i in range(1,n):
    a=stats[i][4]; w0=stats[i][2]; h0=stats[i][3]
    if 150<=a<=2500 and 10<=w0<=45 and 10<=h0<=45:
        cands.append((int(cents[i][0]),int(cents[i][1]),int(a)))
print("corners:", cands[:8])
ok=False
if cands:
    cx,cy,_=cands[0]
    swipe(cx,cy,cx,4,900)
    img,ts=cap("c")
    # 清掉旧导出再导出
    sh(ADB,"-s",DEV,"shell","rm","-f","/sdcard/Download/annot_b01.json")
    sh(ADB,"-s",DEV,"shell","rm","-f","/sdcard/Android/data/com.clashlab.annotator/files/Downloads/annot_b01.json")
    h=find(ts,"导出本张")
    print("export:",h)
    if h:
        tap(h[0],h[1],2.5)
        out=os.path.join(QA,"t_export.json")
        for src in ("/sdcard/Download/annot_b01.json","/sdcard/Android/data/com.clashlab.annotator/files/Downloads/annot_b01.json"):
            if os.path.exists(out): os.remove(out)
            sh(ADB,"-s",DEV,"pull",src,out)
            if os.path.exists(out):
                d=json.load(open(out,encoding="utf-8"))
                cn=d.get("corners_norm") or []
                print("corners_norm:", [[round(v,3) for v in p] for p in cn])
                print("MIN_Y:", min((p[1] for p in cn), default=None))
                ok=True
                break
print("RESULT:", ok)
sh(ADB,"-s",DEV,"shell","wm","size","1920x1080")
