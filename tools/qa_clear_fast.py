# -*- coding: utf-8 -*-
"""快速双击清空按钮（3 秒内），验证 confirm 修复是否生效。"""
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ADB = r"E:\leidian\LDPlayer9\adb.exe"; DEV = "emulator-5554"
QA = os.path.join(BASE, "out", "apk_qa")
def sh(*a, timeout=60): return subprocess.run(list(a), capture_output=True, text=True, timeout=timeout)
def tap(x,y,w=0.0): sh(ADB,"-s",DEV,"shell","input","tap",str(x),str(y));
def cap(tag):
    p="/sdcard/z.png"; sh(ADB,"-s",DEV,"shell","screencap","-p",p)
    dst=os.path.join(QA,tag+".png")
    for _ in range(3):
        sh(ADB,"-s",DEV,"pull",p,dst)
        if os.path.exists(dst) and os.path.getsize(dst)>1000: break
        time.sleep(0.3)
    img=cv2.imdecode(np.fromfile(dst,np.uint8),cv2.IMREAD_COLOR)
    E=RapidOCR(); res,_=E(img)
    return [(b,str(t)) for b,t,_s in (res or [])], dst
def find(ts,key):
    for b,t in ts:
        if key in t:
            xs=[p[0] for p in b]; ys=[p[1] for p in b]
            return int(sum(xs)/4), int(sum(ys)/4)
    return None
ts,_ = cap("clear_before")
print("before:", [t for _b,t in ts if "已标" in t][:2])
hit = find(ts,"清空本张") or (207,1031)
print("clear at:", hit)
tap(hit[0], hit[1]); time.sleep(0.5)
tap(hit[0], hit[1]); time.sleep(1.0)
ts,_ = cap("clear_after")
print("after:", [t for _b,t in ts if "已标" in t][:2], "| toast:", [t for _b,t in ts if "清空" in t][:2])
