# -*- coding: utf-8 -*-
"""QA 补测：撤销 / 点删 / 清空（confirm 是否生效）/ 帮助弹层。"""
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ADB = r"E:\leidian\LDPlayer9\adb.exe"; DEV = "emulator-5554"
QA = os.path.join(BASE, "out", "apk_qa"); seqi=[400]
def sh(*a, timeout=60): return subprocess.run(list(a), capture_output=True, text=True, timeout=timeout)
def tap(x,y,w=0.9): sh(ADB,"-s",DEV,"shell","input","tap",str(x),str(y)); time.sleep(w)
def texts(tag):
    seqi[0]+=1; p="/sdcard/s_%d.png"%seqi[0]
    sh(ADB,"-s",DEV,"shell","screencap","-p",p)
    dst=os.path.join(QA,"%s_%d.png"%(tag,seqi[0]))
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
# 回到第1张并确认有 2 栋
ts,_=texts("start")
print("start:", [t for _b,t in ts if "已标" in t or "/20" in t][:3])
# 撤销一次
hit=find(ts,"撤销")
if hit: tap(hit[0],hit[1],1.0)
ts,_=texts("after_undo")
print("after undo:", [t for _b,t in ts if "已标" in t][:2])
# 点删：再点一次已有标记位置
tap(960,480,1.0)
ts,_=texts("after_delete")
print("after tap existing:", [t for _b,t in ts if "已标" in t][:2])
# 清空（应弹 confirm；WebView 默认可能不显示）
hit=find(ts,"清空本张")
if hit:
    tap(hit[0],hit[1],1.5)
ts,_=texts("after_clear")
print("after clear:", [t for _b,t in ts if "已标" in t][:2])
# 帮助
hit=find(ts,"怎么用")
if hit: tap(hit[0],hit[1],1.2)
ts,_=texts("help")
print("help shown:", any("30 秒" in t or "第 1 步" in t for _b,t in ts))
