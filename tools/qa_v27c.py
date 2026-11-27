# -*- coding: utf-8 -*-
"""v0.2.7 真机重测（固定坐标）：4 角 → 拖左上角到顶边 → 导出看 min_y。"""
import json, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ADB = r"E:\leidian\LDPlayer9\adb.exe"; DEV = "emulator-5554"; QA=os.path.join(BASE,"out","apk_qa")
def sh(*a, timeout=60):
    try: return subprocess.run(list(a), capture_output=True, text=True, timeout=timeout)
    except Exception: return None
def tap(x,y,w=0.55): sh(ADB,"-s",DEV,"shell","input","tap",str(int(x)),str(int(y))); time.sleep(w)
def swipe(x1,y1,x2,y2,ms=900): sh(ADB,"-s",DEV,"shell","input","swipe",str(int(x1)),str(int(y1)),str(int(x2)),str(int(y2)),str(ms)); time.sleep(1.6)
def cap(tag):
    p="/sdcard/u_%s.png"%tag; sh(ADB,"-s",DEV,"shell","screencap","-p",p)
    dst=os.path.join(QA,"u_%s.png"%tag)
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
sh(ADB,"-s",DEV,"shell","wm","size","1920x864"); time.sleep(1.2)
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
# 固定四角（图片约 x326..1571, y279..851）
for pt in ((400,340),(1490,340),(1490,800),(400,800)):
    tap(pt[0],pt[1],0.55)
img,ts=cap("b")
print("hint:", [t for _b,t in ts if "已点" in t][:1])
# 拖左上角(400,340)到顶边
swipe(400,340,400,4,1000)
img,ts=cap("c")
print("after drag hint:", [t for _b,t in ts if "已点" in t][:1])
# 清旧文件后导出
sh(ADB,"-s",DEV,"shell","rm","-f","/sdcard/Download/annot_b01.json")
sh(ADB,"-s",DEV,"shell","rm","-f","/sdcard/Android/data/com.clashlab.annotator/files/Downloads/annot_b01.json")
h=find(ts,"导出本张")
print("export btn:",h)
if h:
    tap(h[0],h[1],2.5)
    out=os.path.join(QA,"u_export.json")
    if os.path.exists(out): os.remove(out)
    for src in ("/sdcard/Download/annot_b01.json","/sdcard/Android/data/com.clashlab.annotator/files/Downloads/annot_b01.json"):
        if os.path.exists(out): os.remove(out)
        sh(ADB,"-s",DEV,"pull",src,out)
        if os.path.exists(out):
            d=json.load(open(out,encoding="utf-8"))
            cn=d.get("corners_norm") or []
            print("corners_norm:", [[round(v,3) for v in p] for p in cn])
            print("MIN_Y:", min((p[1] for p in cn), default=None))
            break
sh(ADB,"-s",DEV,"shell","wm","size","1920x1080")
