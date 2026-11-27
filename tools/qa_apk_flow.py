# -*- coding: utf-8 -*-
"""APK 功能实测：用 adb 点击驱动标注流程，并截图/OCR 校验。"""
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ADB = r"E:\leidian\LDPlayer9\adb.exe"; DEV = "emulator-5554"
QA = os.path.join(BASE, "out", "apk_qa")
os.makedirs(QA, exist_ok=True)
def sh(*a, timeout=60):
    return subprocess.run(list(a), capture_output=True, text=True, timeout=timeout)
def tap(x, y, wait=0.9):
    sh(ADB, "-s", DEV, "shell", "input", "tap", str(x), str(y)); time.sleep(wait)
def shot(tag):
    p = "/sdcard/s.png"
    sh(ADB, "-s", DEV, "shell", "screencap", "-p", p)
    dst = os.path.join(QA, tag + ".png")
    sh(ADB, "-s", DEV, "pull", p, dst)
    img = cv2.imdecode(np.fromfile(dst, np.uint8), cv2.IMREAD_COLOR)
    E = RapidOCR(); res, _ = E(img)
    return img, [(b, str(t)) for b, t, _s in (res or [])]
def find(texts, key):
    for b, t in texts:
        if key in t:
            xs = [p[0] for p in b]; ys = [p[1] for p in b]
            return int(sum(xs)/4), int(sum(ys)/4)
    return None
# 1) 点四角（图片显示区域约 560..1355 x 280..640）
for x, y in ((600, 470), (1330, 470), (960, 630), (600, 470)):
    pass
corners = [(600, 470), (1330, 470), (960, 630), (600, 470)]
# 正确的菱形四角：左、上、右、下
tap(600, 470); tap(960, 290); tap(1330, 470); tap(960, 630)
img, texts = shot("calib")
print("after calib:", [t for _b, t in texts if "已" in t or "张" in t][:4])
# 2) 选 防空火箭（左上第一个类型按钮）
tap(95, 710, 0.6)
# 3) 放两个建筑
tap(960, 480, 0.8)
tap(820, 520, 0.8)
img, texts = shot("placed")
cnt = [t for _b, t in texts if "已标" in t]
print("count:", cnt)
# 4) 导出本张
hit = find(texts, "导出本张")
print("export btn:", hit)
if hit:
    tap(hit[0], hit[1], 1.5)
img, texts = shot("exported")
print("toast:", [t for _b, t in texts if "导出" in t or "保存" in t][:3])
# 5) 下一张
hit = find(texts, "下一张")
print("next btn:", hit)
if hit:
    tap(hit[0], hit[1], 1.2)
img, texts = shot("next")
print("next page:", [t for _b, t in texts if "第" in t or "已标" in t][:4])
# 6) 导出全部
hit = find(texts, "导出全部")
print("export all:", hit)
if hit:
    tap(hit[0], hit[1], 1.5)
img, texts = shot("export_all")
print("toast2:", [t for _b, t in texts if "导出" in t or "还没有" in t][:3])
# 7) 文件检查
r = sh(ADB, "-s", DEV, "shell", "ls", "-l", "/sdcard/Download")
print("downloads:", r.stdout.strip()[:400])
