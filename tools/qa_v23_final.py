# -*- coding: utf-8 -*-
"""v0.2.3 最终冒烟：短屏 + 四角 + 列表 + 缩放 + 平移 + 导出。"""
import json, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ADB = r"E:\leidian\LDPlayer9\adb.exe"; DEV = "emulator-5554"; QA = os.path.join(BASE,"out","apk_qa")
def sh(*a, timeout=60): return subprocess.run(list(a), capture_output=True, text=True, timeout=timeout)
def tap(x,y,w=0.55): sh(ADB,"-s",DEV,"shell","input","tap",str(int(x)),str(int(y))); time.sleep(w)
def cap(tag):
    p="/sdcard/f_%s.png"%tag; sh(ADB,"-s",DEV,"shell","screencap","-p",p)
    dst=os.path.join(QA,"f_%s.png"%tag)
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
print(sh(ADB,"-s",DEV,"install","-r",r"E:\ClashLab\android\dist\ClashLabAnnotator_v23.apk").stdout.strip())
sh(ADB,"-s",DEV,"shell","pm","clear","com.clashlab.annotator")
sh(ADB,"-s",DEV,"shell","pm","grant","com.clashlab.annotator","android.permission.WRITE_EXTERNAL_STORAGE")
sh(ADB,"-s",DEV,"shell","am","start","-n","com.clashlab.annotator/.MainActivity")
time.sleep(3)
img,ts=cap("a")
h=find(ts,"知道了")
if h: tap(h[0],h[1],0.8)
# 四角
for p in [(575,525),(955,265),(1345,525),(955,760)]: tap(p[0],p[1],0.5)
img,ts=cap("b")
print("hint:",[t for _b,t in ts if "已点" in t][:1], "| pal:", any("防御" in t for _b,t in ts))
# 选防空 + 放
h=find(ts,"防空")
if h: tap(h[0],h[1],0.5)
tap(960,540,0.8)
img,ts=cap("c")
print("count:",[t for _b,t in ts if "已标" in t][:1])
# 放大两次
h=find(ts,"＋")
if h:
    tap(h[0],h[1],0.5); tap(h[0],h[1],0.5)
# 平移：从右往左拖 250px
sh(ADB,"-s",DEV,"shell","input","swipe","1200","500","950","500","500"); time.sleep(1.2)
img,ts=cap("d")
# 缩小回适应
h=find(ts,"适应")
if h: tap(h[0],h[1],0.6)
# 导出
h=find(ts,"导出本张")
if h: tap(h[0],h[1],2.0)
out=os.path.join(QA,"f_export.json")
if os.path.exists(out): os.remove(out)
for src in ("/sdcard/Download/annot_b01.json",
            "/sdcard/Android/data/com.clashlab.annotator/files/Downloads/annot_b01.json"):
    if os.path.exists(out): os.remove(out)
    sh(ADB,"-s",DEV,"pull",src,out)
    if os.path.exists(out):
        d=json.load(open(out,encoding="utf-8"))
        if d.get("version")==2 and d.get("buildings"):
            print("EXPORT OK | size:",d.get("image_size"),"| norm:",d.get("corners_norm") is not None,
                  "| bld:",[(b.get("name"),b.get("tile")) for b in d.get("buildings") or []])
            break
