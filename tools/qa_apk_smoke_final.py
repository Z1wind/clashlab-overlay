# -*- coding: utf-8 -*-
"""最终 APK 冒烟：安装→启动→教程→标定→放点→清空→导出，并校验提示。"""
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ADB = r"E:\leidian\LDPlayer9\adb.exe"; DEV = "emulator-5554"
QA = os.path.join(BASE, "out", "apk_qa"); seqi=[1300]
def sh(*a, timeout=90): return subprocess.run(list(a), capture_output=True, text=True, timeout=timeout)
def tap(x,y,w=1.0): sh(ADB,"-s",DEV,"shell","input","tap",str(x),str(y)); time.sleep(w)
def cap(tag):
    seqi[0]+=1; p="/sdcard/f_%d.png"%seqi[0]
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
apk = r"E:\ClashLab\android\dist\ClashLabAnnotator_v20.apk"
print(sh(ADB,"-s",DEV,"install","-r",apk).stdout.strip())
sh(ADB,"-s",DEV,"shell","pm","clear","com.clashlab.annotator")
sh(ADB,"-s",DEV,"shell","pm","grant","com.clashlab.annotator","android.permission.WRITE_EXTERNAL_STORAGE")
sh(ADB,"-s",DEV,"shell","am","start","-n","com.clashlab.annotator/.MainActivity")
time.sleep(3)
ts = cap("smoke_launch")
print("help auto:", any("30" in t for _b,t in ts), "| 知道了:", find(ts,"知道了"))
hit = find(ts,"知道了")
if hit: tap(hit[0],hit[1],0.8)
# 标定 + 放 2
tap(600,470,0.5); tap(960,290,0.5); tap(1330,470,0.5); tap(960,630,0.8)
tap(95,760,0.5); tap(900,480,0.6); tap(1020,500,0.6)
ts = cap("smoke_placed")
print("placed:", [t for _b,t in ts if "已标" in t][:2])
# 导出（提示友好文本）
hit = find(ts,"导出本张")
if hit: tap(hit[0],hit[1],1.6)
ts = cap("smoke_export")
print("export toast:", [t for _b,t in ts if "保存" in t or "下载" in t or "失败" in t][:3])
# 清空（快速双击）
hit = find(ts,"清空本张") or (207,1031)
tap(hit[0],hit[1],0); time.sleep(0.4); tap(hit[0],hit[1],1.0)
ts = cap("smoke_clear")
print("cleared:", [t for _b,t in ts if "已标" in t or "清空" in t][:3])
# 文件
r = sh(ADB,"-s",DEV,"shell","ls","-l","/sdcard/Download/annot_b01.json")
print("file:", r.stdout.strip()[:160])
