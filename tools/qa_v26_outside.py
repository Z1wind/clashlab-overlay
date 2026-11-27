# -*- coding: utf-8 -*-
"""v0.2.6 QA：四角可拖出图片边界。"""
import json, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ADB = r"E:\leidian\LDPlayer9\adb.exe"; DEV = "emulator-5554"; QA=os.path.join(BASE,"out","apk_qa")
def sh(*a, timeout=60): return subprocess.run(list(a), capture_output=True, text=True, timeout=timeout)
def tap(x,y,w=0.5): sh(ADB,"-s",DEV,"shell","input","tap",str(int(x)),str(int(y))); time.sleep(w)
def swipe(x1,y1,x2,y2,ms=600): sh(ADB,"-s",DEV,"shell","input","swipe",str(int(x1)),str(int(y1)),str(int(x2)),str(int(y2)),str(ms)); time.sleep(1.2)
def cap(tag):
    p="/sdcard/m_%s.png"%tag; sh(ADB,"-s",DEV,"shell","screencap","-p",p)
    dst=os.path.join(QA,"m_%s.png"%tag)
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
print(sh(ADB,"-s",DEV,"install","-r",r"E:\ClashLab\android\dist\ClashLabAnnotator_v26.apk").stdout.strip())
sh(ADB,"-s",DEV,"shell","pm","clear","com.clashlab.annotator")
sh(ADB,"-s",DEV,"shell","pm","grant","com.clashlab.annotator","android.permission.WRITE_EXTERNAL_STORAGE")
sh(ADB,"-s",DEV,"shell","am","start","-n","com.clashlab.annotator/.MainActivity")
time.sleep(4)
img,ts=cap("a")
h=find(ts,"知道了")
if h: tap(h[0],h[1],1.0)
time.sleep(1)
img,ts=cap("b")
print("help gone:", not any("30秒上手" in t for _b,t in ts))
# 四角：点在画布四角附近（任意位置即可）
for p in [(600,500),(1200,350),(1200,700),(600,650)]:
    tap(p[0],p[1],0.5)
img,ts=cap("c")
print("hint:", [t for _b,t in ts if "已点" in t][:1])
# 找黄色角点
hsv=cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
mask=cv2.inRange(hsv,(18,120,160),(40,255,255))
n, lab, stats, cents = cv2.connectedComponentsWithStats(mask, 8)
pts=[]
for i in range(1,n):
    a=stats[i][4]
    if 40<=a<=2000: pts.append(tuple(map(int,cents[i])))
print("yellow markers:", pts[:6])
if len(pts)>=1:
    x0,y0=pts[0]
    # 把第1个角拖到图片左外侧：向左 400px
    swipe(x0,y0,max(60,x0-420),y0,700)
    img,ts=cap("d")
# 导出本张（前提: 已标定 4 角）
h=find(ts,"导出本张")
print("export:",h)
if h: tap(h[0],h[1],2.0)
out=os.path.join(QA,"m_export.json")
if os.path.exists(out): os.remove(out)
for src in ("/sdcard/Download/annot_b01.json","/sdcard/Android/data/com.clashlab.annotator/files/Downloads/annot_b01.json"):
    if os.path.exists(out): os.remove(out)
    sh(ADB,"-s",DEV,"pull",src,out)
    if os.path.exists(out):
        d=json.load(open(out,encoding="utf-8"))
        if d.get("version")==2:
            cn=d.get("corners_norm") or []
            print("corners_norm:", cn)
            print("has_outside:", any((p[0]<0 or p[0]>1 or p[1]<0 or p[1]>1) for p in cn))
            break
