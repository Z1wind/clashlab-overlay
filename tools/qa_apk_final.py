# -*- coding: utf-8 -*-
"""权限已授予，跑完整回归。"""
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ADB = r"E:\leidian\LDPlayer9\adb.exe"; DEV = "emulator-5554"
QA = os.path.join(BASE, "out", "apk_qa"); seqi=[1100]
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
ts = cap("g0")
hit = find(ts, "知道了")
if hit: tap(hit[0], hit[1], 1.0)
ts = cap("g1")
print("UI:", [t for _b,t in ts if "已标" in t or "/20" in t][:3])
print("=== 标定 + 放2栋 ===")
tap(600,470); tap(960,290); tap(1330,470); tap(960,630)
ts = cap("g2")
print("hint:", [t for _b,t in ts if "已标" in t][:2])
tap(95,760,0.6)
tap(900,480,0.8); tap(1020,500,0.8)
ts = cap("g3")
print("placed:", [t for _b,t in ts if "已标" in t][:2])
print("=== 清空双段确认 ===")
hit = find(ts, "清空本张")
print("clear:", hit)
if hit:
    tap(hit[0], hit[1], 0.8)
    ts = cap("g4")
    print("armed:", [t for _b,t in ts if "再点" in t][:2])
    hit2 = find(ts, "再点一次")
    if hit2: tap(hit2[0], hit2[1], 1.0)
    ts = cap("g5")
    print("cleared:", [t for _b,t in ts if "已标" in t][:2])
print("=== 重标+导出 ===")
tap(600,470); tap(960,290); tap(1330,470); tap(960,630)
tap(95,760,0.6); tap(960,480,0.9)
ts = cap("g6")
hit = find(ts, "导出本张")
print("export:", hit)
if hit: tap(hit[0], hit[1], 1.6)
ts = cap("g7")
print("toast:", [t for _b,t in ts if "已导出" in t or "Downloads" in t][:3])
r = sh(ADB,"-s",DEV,"shell","ls","-l","/sdcard/Download/annot_b01.json")
print(r.stdout.strip()[:200])
