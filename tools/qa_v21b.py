# -*- coding: utf-8 -*-
"""v21 QA 修正版：画布检测只看舞台区域，四角用菱形比例，拖动后导出校验。"""
import json, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ADB = r"E:\leidian\LDPlayer9\adb.exe"; DEV = "emulator-5554"; QA = os.path.join(BASE, "out", "apk_qa")
def sh(*a, timeout=60): return subprocess.run(list(a), capture_output=True, text=True, timeout=timeout)
def tap(x,y,w=0.7): sh(ADB,"-s",DEV,"shell","input","tap",str(int(x)),str(int(y))); time.sleep(w)
def swipe(x1,y1,x2,y2,ms=500): sh(ADB,"-s",DEV,"shell","input","swipe",str(int(x1)),str(int(y1)),str(int(x2)),str(int(y2)),str(ms)); time.sleep(1.2)
def cap(tag):
    p="/sdcard/v2_%s.png"%tag; sh(ADB,"-s",DEV,"shell","screencap","-p",p)
    dst=os.path.join(QA,"v2_%s.png"%tag)
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
img,ts=cap("a")
h=find(ts,"知道了")
if h: tap(h[0],h[1],1.0)
img,ts=cap("b")
# 舞台区域：y 150..650，找亮色图像区域
sub=img[150:660,:,:]
g=cv2.cvtColor(sub,cv2.COLOR_BGR2GRAY)
mask=(g>70).astype(np.uint8)
cols=mask.sum(0); rows=mask.sum(1)
thc=max(20, sub.shape[0]*0.15); thr=max(20, sub.shape[1]*0.15)
xs=np.nonzero(cols>thc)[0]; ys=np.nonzero(rows>thr)[0]
print("xs range:", (xs.min(), xs.max()) if len(xs) else None, "ys:", (ys.min(),ys.max()) if len(ys) else None)
x0,x1=int(xs.min()),int(xs.max()); y0,y1=int(ys.min())+150,int(ys.max())+150
W=x1-x0; H=y1-y0
print("image bbox:",x0,y0,x1,y1,"size:",W,H)
# 菱形四角（相对图像：左/上/右/下）
L=(x0+0.18*W, y0+0.52*H); T=(x0+0.50*W, y0+0.08*H); R=(x0+0.82*W, y0+0.52*H); B=(x0+0.50*W, y0+0.92*H)
print("corner taps:", [tuple(map(int,p)) for p in (L,T,R,B)])
for p in (L,T,R,B): tap(p[0],p[1],0.5)
img,ts=cap("c")
print("hint:",[t for _b,t in ts if "已点" in t][:2])
# 选类型：点「防空」按钮
pt=find(ts,"防空")
print("palette 防空:",pt)
if pt: tap(pt[0],pt[1],0.5)
# 放一栋（中间偏上）
tap(x0+0.5*W, y0+0.45*H, 0.8)
img,ts=cap("d")
print("count:",[t for _b,t in ts if "已标" in t][:2])
# 拖动第1角 +60,+40
sx,sy=L
swipe(sx,sy,sx+60,sy+40,500)
img,ts=cap("e")
# 截图里读不到角点，直接导出校验
h=find(ts,"导出本张")
print("export btn:",h)
if h: tap(h[0],h[1],1.8)
out=os.path.join(QA,"v2_annot_b01.json")
if os.path.exists(out): os.remove(out)
sh(ADB,"-s",DEV,"pull","/sdcard/Download/annot_b01.json",out)
if os.path.exists(out):
    d=json.load(open(out,encoding="utf-8"))
    print("version:",d.get("version"),"| image_size:",d.get("image_size"),"| corners:",d.get("corners"))
    print("corners_norm:",d.get("corners_norm"))
    print("buildings:",[(b.get("name"),b.get("tile")) for b in d.get("buildings") or []])
else:
    print("no export")
