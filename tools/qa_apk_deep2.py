# -*- coding: utf-8 -*-
"""APK 深度 QA 补测：翻页遍历 + 导出全部 + logcat。"""
import json, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ADB = r"E:\leidian\LDPlayer9\adb.exe"; DEV = "emulator-5554"
QA = os.path.join(BASE, "out", "apk_qa")
seqi = [0]
def sh(*a, timeout=60):
    return subprocess.run(list(a), capture_output=True, text=True, timeout=timeout)
def tap(x, y, wait=1.0):
    sh(ADB, "-s", DEV, "shell", "input", "tap", str(x), str(y)); time.sleep(wait)
def shot_texts(tag):
    seqi[0] += 1
    p = "/sdcard/s_%03d.png" % seqi[0]
    sh(ADB, "-s", DEV, "shell", "screencap", "-p", p)
    dst = os.path.join(QA, "%s_%03d.png" % (tag, seqi[0]))
    for _ in range(3):
        sh(ADB, "-s", DEV, "pull", p, dst)
        if os.path.exists(dst) and os.path.getsize(dst) > 1000:
            break
        time.sleep(0.3)
    img = cv2.imdecode(np.fromfile(dst, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return []
    E = RapidOCR(); res, _ = E(img)
    return [(b, str(t)) for b, t, _s in (res or [])]
def find(texts, key):
    for b, t in texts:
        if key in t:
            xs = [p[0] for p in b]; ys = [p[1] for p in b]
            return int(sum(xs)/4), int(sum(ys)/4)
    return None

print("=== 翻页遍历 1→20 ===")
pages_ok = 0
for k in range(1, 20):
    texts = shot_texts("pg")
    label = [t for _b, t in texts if "/20" in t]
    if label:
        pages_ok += 1
        if k % 5 == 0:
            print(" page:", label[0])
    hit = find(texts, "下一张")
    if not hit:
        print(" no next at step", k); break
    tap(hit[0], hit[1], 1.0)
texts = shot_texts("last")
print("last:", [t for _b, t in texts if "/20" in t][:2], "| pages checked:", pages_ok)
# 最后一张也标定+放一个，用于导出全部 2 张
tap(600, 470); tap(960, 290); tap(1330, 470); tap(960, 630)
texts = shot_texts("last_calib")
hit = find(texts, "地狱塔") or find(texts, "加农炮")
if hit:
    tap(hit[0], hit[1], 0.6)
tap(960, 480, 0.9)
texts = shot_texts("last_placed")
print("last count:", [t for _b, t in texts if "已标" in t][:2])
hit = find(texts, "导出全部")
if hit:
    tap(hit[0], hit[1], 1.6)
p = os.path.join(QA, "annot_all2.json")
sh(ADB, "-s", DEV, "pull", "/sdcard/Download/annot_all.json", p)
if os.path.exists(p):
    d = json.load(open(p, encoding="utf-8"))
    print("bundle:", d.get("count"), "bases:", [(b["image"], len(b["buildings"])) for b in d.get("bases") or []])
print("=== logcat ===")
r = sh(ADB, "-s", DEV, "logcat", "-d", "-t", "600")
bad = [ln for ln in (r.stdout or "").splitlines() if any(k in ln for k in ("Uncaught", "CONSOLE ERROR", "AndroidRuntime", "FATAL"))]
print("\n".join(bad[-10:]) if bad else "no JS/runtime errors")
