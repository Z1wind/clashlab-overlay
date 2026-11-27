# -*- coding: utf-8 -*-
"""v21 QA 简版：已知坐标四角 → 放建筑 → 拖动角 → 导出校验。"""
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
    p="/sdcard/w_%s.png"%tag; sh(ADB,"-s",DEV,"shell","screencap","-p",p)
    dst=os.path.join(QA,"w_%s.png"%tag)
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
h=find(ts,"重设四角")
if h: tap(h[0],h[1],0.8)
# 已知坐标（v0.2.0 验证过）
pts=[(600,470),(960,290),(1330,470),(960,630)]
for p in pts: tap(p[0],p[1],0.5)
img,ts=cap("b")
print("hint:",[t for _b,t in ts if "已点" in t][:2])
# 选防空 + 放两栋
h=find(ts,"防空")
if h: tap(h[0],h[1],0.5)
tap(960,420,0.8); tap(820,470,0.8)
img,ts=cap("c")
print("count:",[t for _b,t in ts if "已标" in t][:2])
# 拖动第 1 个角 (600,470) -> (660,510)
swipe(600,470,660,510,500)
img,ts=cap("d")
# 导出
h=find(ts,"导出本张")
print("export:",h)
if h: tap(h[0],h[1],1.8)
out=os.path.join(QA,"w_annot_b01.json")
if os.path.exists(out): os.remove(out)
sh(ADB,"-s",DEV,"pull","/sdcard/Download/annot_b01.json",out)
if os.path.exists(out):
    d=json.load(open(out,encoding="utf-8"))
    print("version:",d.get("version"),"| size:",d.get("image_size"),"| corners:",d.get("corners"))
    print("norm:",d.get("corners_norm"))
    print("buildings:",[(b.get("name"),b.get("tile")) for b in d.get("buildings") or []])
else: print("no export")
