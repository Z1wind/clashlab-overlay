# -*- coding: utf-8 -*-
"""处理权限弹窗后继续回归。"""
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ADB = r"E:\leidian\LDPlayer9\adb.exe"; DEV = "emulator-5554"
QA = os.path.join(BASE, "out", "apk_qa"); seqi=[900]
def sh(*a, timeout=60): return subprocess.run(list(a), capture_output=True, text=True, timeout=timeout)
def tap(x,y,w=1.0): sh(ADB,"-s",DEV,"shell","input","tap",str(x),str(y)); time.sleep(w)
def cap(tag):
    seqi[0]+=1; p="/sdcard/q_%d.png"%seqi[0]
    sh(ADB,"-s",DEV,"shell","screencap","-p",p)
    dst=os.path.join(QA,"%s_%d.png"%(tag,seqi[0]))
    for _ in range(3):
        sh(ADB,"-s",DEV,"pull",p,dst)
        if os.path.exists(dst) and os.path.getsize(dst)>1000: break
        time.sleep(0.3)
    img=cv2.imdecode(np.fromfile(dst,np.uint8),cv2.IMREAD_COLOR)
    E=RapidOCR(); res,_=E(img)
    return [(b,str(t)) for b,t,_s in (res or [])]
def find(ts,key):
    for b,t in ts:
        if key in t:
            xs=[p[0] for p in b]; ys=[p[1] for p in b]
            return int(sum(xs)/4), int(sum(ys)/4)
    return None
ts = cap("perm")
print("permission dialog:", any("允许" in t for _b,t in ts), "| texts:", [t for _b,t in ts if "允许" in t or "拒绝" in t][:3])
hit = find(ts, "允许")
if hit:
    tap(hit[0], hit[1], 1.2)
ts = cap("help2")
print("help still:", any("30" in t for _b,t in ts), "| 知道了:", find(ts,"知道了"))
hit = find(ts, "知道了")
if hit: tap(hit[0], hit[1], 1.0)
ts = cap("ui")
print("UI texts:", [t for _b,t in ts if "已标" in t or "/20" in t][:3])
print("=== 标定+放2栋 ===")
tap(600,470); tap(960,290); tap(1330,470); tap(960,630)
ts = cap("calib_ok")
print("hint:", [t for _b,t in ts if "已标" in t][:2])
tap(95,760,0.6); tap(900,480,0.8); tap(1020,500,0.8)
ts = cap("placed_ok")
print("placed:", [t for _b,t in ts if "已标" in t][:2])
print("=== 清空双段 ===")
hit = find(ts, "清空本张")
print("clear:", hit)
if hit:
    tap(hit[0], hit[1], 0.8)
    ts = cap("armed")
    print("armed:", [t for _b,t in ts if "再点" in t][:2])
    hit2 = find(ts, "再点一次")
    if hit2: tap(hit2[0], hit2[1], 1.0)
    ts = cap("cleared")
    print("cleared:", [t for _b,t in ts if "已标" in t][:2])
print("=== 重标+导出 ===")
tap(600,470); tap(960,290); tap(1330,470); tap(960,630)
tap(95,760,0.6); tap(960,480,0.9)
ts = cap("ready_export")
hit = find(ts, "导出本张")
print("export btn:", hit)
if hit: tap(hit[0], hit[1], 1.5)
ts = cap("exported")
print("toast:", [t for _b,t in ts if "已导出" in t or "Downloads" in t][:3])
r = sh(ADB,"-s",DEV,"shell","ls","-l","/sdcard/Download")
print(r.stdout.strip()[:400])
