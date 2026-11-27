# -*- coding: utf-8 -*-
"""v21 QA：四角拖动 + 中文标点 + v2 导出。"""
import json, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ADB = r"E:\leidian\LDPlayer9\adb.exe"; DEV = "emulator-5554"; QA = os.path.join(BASE, "out", "apk_qa")
def sh(*a, timeout=60): return subprocess.run(list(a), capture_output=True, text=True, timeout=timeout)
def tap(x,y,w=0.8): sh(ADB,"-s",DEV,"shell","input","tap",str(int(x)),str(int(y))); time.sleep(w)
def swipe(x1,y1,x2,y2,ms=400): sh(ADB,"-s",DEV,"shell","input","swipe",str(int(x1)),str(int(y1)),str(int(x2)),str(int(y2)),str(ms)); time.sleep(1.0)
def cap(tag):
    p="/sdcard/v21_%s.png"%tag; sh(ADB,"-s",DEV,"shell","screencap","-p",p)
    dst=os.path.join(QA,"v21_%s.png"%tag)
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
img,ts = cap("a")
h=find(ts,"知道了")
if h: tap(h[0],h[1],1.0)
img,ts = cap("b")
# 找画布区域（stage 非黑区域）
hsv=cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
mask=(hsv[:,:,2]>40).astype(np.uint8)
mask[:150,:]=0; mask[880:,:]=0; mask[:, :10]=0; mask[:, -10:]=0
ys,xs=np.nonzero(mask)
x0,x1,y0,y1=int(xs.min()),int(xs.max()),int(ys.min()),int(ys.max())
print("canvas bbox:",x0,y0,x1,y1)
W=x1-x0; H=y1-y0
corners=[(x0+0.5*W,y0+0.06*H),(x0+0.94*W,y0+0.5*H),(x0+0.5*W,y0+0.94*H),(x0+0.06*W,y0+0.5*H)]  # T,R,B,L
for (x,y) in corners: tap(x,y,0.5)
img,ts=cap("c")
print("hint:",[t for _b,t in ts if "已标" in t or "标定" in t][:2])
# 选一个中文类型（点第一个按钮）并放一栋
pt=find(ts,"防空")
if pt: tap(pt[0],pt[1],0.5)
tap(x0+0.5*W, y0+0.5*H, 0.8)
img,ts=cap("d")
print("count:",[t for _b,t in ts if "已标" in t][:2])
# 拖动第 1 个角（T）向右下 +60,+40
sx,sy=corners[0]
swipe(sx,sy,sx+60,sy+40,500)
img,ts=cap("e")
# 导出
h=find(ts,"导出本张")
print("export:",h)
if h: tap(h[0],h[1],1.8)
# 校验导出 JSON
out=os.path.join(QA,"v21_annot_b01.json")
sh(ADB,"-s",DEV,"pull","/sdcard/Download/annot_b01.json",out)
if os.path.exists(out):
    d=json.load(open(out,encoding="utf-8"))
    print("json version:",d.get("version"),"| image_size:",d.get("image_size"),"| corners:",d.get("corners"),"| norm:",d.get("corners_norm"))
    print("buildings:",[(b.get("name"),b.get("tile")) for b in d.get("buildings") or []])
else:
    print("no export file")
