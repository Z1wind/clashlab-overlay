# -*- coding: utf-8 -*-
"""APK 深度 QA：JSON 校验、边界用例、翻页遍历、持久化、logcat。"""
import json, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ADB = r"E:\leidian\LDPlayer9\adb.exe"; DEV = "emulator-5554"
QA = os.path.join(BASE, "out", "apk_qa")
def sh(*a, timeout=60):
    return subprocess.run(list(a), capture_output=True, text=True, timeout=timeout)
def tap(x, y, wait=0.9):
    sh(ADB, "-s", DEV, "shell", "input", "tap", str(x), str(y)); time.sleep(wait)
def pull(name):
    dst = os.path.join(QA, name)
    sh(ADB, "-s", DEV, "pull", "/sdcard/Download/" + name, dst)
    return dst
def shot_texts(tag):
    p = "/sdcard/s.png"
    sh(ADB, "-s", DEV, "shell", "screencap", "-p", p)
    dst = os.path.join(QA, tag + ".png")
    sh(ADB, "-s", DEV, "pull", p, dst)
    img = cv2.imdecode(np.fromfile(dst, np.uint8), cv2.IMREAD_COLOR)
    E = RapidOCR(); res, _ = E(img)
    return [(b, str(t)) for b, t, _s in (res or [])]
def find(texts, key):
    for b, t in texts:
        if key in t:
            xs = [p[0] for p in b]; ys = [p[1] for p in b]
            return int(sum(xs)/4), int(sum(ys)/4)
    return None

print("=== 1. JSON 内容校验 ===")
for name in ("annot_b01.json", "annot_all.json"):
    p = pull(name)
    if not os.path.exists(p):
        print(name, "MISSING"); continue
    d = json.load(open(p, encoding="utf-8"))
    if "bases" in d:
        b = d["bases"][0]
        print(name, "bundle count:", d.get("count"), "| base img:", b["image"],
              "| corners:", len(b["corners"]), "| buildings:", len(b["buildings"]),
              "| types:", sorted({x["type"] for x in b["buildings"]}))
    else:
        print(name, "| img:", d.get("image"), "| corners:", len(d.get("corners") or []),
              "| buildings:", len(d.get("buildings") or []),
              "| tile sample:", (d.get("buildings") or [{}])[0].get("tile"))
    # 坐标合法性
    bad = [x for x in (d.get("buildings") or []) if not (0 <= x["tile"][0] <= 43 and 0 <= x["tile"][1] <= 43)]
    print("  out-of-range tiles:", len(bad))

print("=== 2. 无标定导出（第2张应被拦截） ===")
before = sh(ADB, "-s", DEV, "shell", "ls", "/sdcard/Download").stdout
texts = shot_texts("edge_nocal")
for keys in ("导出本张",):
    hit = find(texts, keys)
    if hit:
        tap(hit[0], hit[1], 1.2)
texts2 = shot_texts("edge_nocal_after")
print("toast:", [t for _b, t in texts2 if "不能" in t or "还没" in t][:3])
after = sh(ADB, "-s", DEV, "shell", "ls", "/sdcard/Download").stdout
print("file list changed:", before.strip() != after.strip())

print("=== 3. 换类型放置（第2张先标定再放加农炮） ===")
# 标定第2张
tap(600, 470); tap(960, 290); tap(1330, 470); tap(960, 630)
texts = shot_texts("p2_calib")
hit = find(texts, "加农炮")
print("cannon btn:", hit)
if hit:
    tap(hit[0], hit[1], 0.6)
tap(960, 480, 0.8)
texts = shot_texts("p2_placed")
print("count:", [t for _b, t in texts if "已标" in t][:2])
hit = find(texts, "导出本张")
if hit:
    tap(hit[0], hit[1], 1.5)
p = pull("annot_b02.json")
if os.path.exists(p):
    d = json.load(open(p, encoding="utf-8"))
    print("b02 types:", [x["type"] for x in d.get("buildings") or []])

print("=== 4. 持久化（重启后第2张仍应有标记） ===")
sh(ADB, "-s", DEV, "shell", "am", "force-stop", "com.clashlab.annotator")
sh(ADB, "-s", DEV, "shell", "am", "start", "-n", "com.clashlab.annotator/.MainActivity")
time.sleep(3)
texts = shot_texts("restart")
print("restart texts:", [t for _b, t in texts if "已标" in t or "第" in t][:3])

print("=== 5. 翻页遍历（到第 20 张） ===")
for _ in range(19):
    texts = shot_texts("pg")
    hit = find(texts, "下一张")
    if not hit:
        print("no next button"); break
    tap(hit[0], hit[1], 1.0)
texts = shot_texts("last")
print("last page:", [t for _b, t in texts if "第" in t][:3])

print("=== 6. logcat 错误 ===")
r = sh(ADB, "-s", DEV, "logcat", "-d", "-t", "400")
lines = [ln for ln in (r.stdout or "").splitlines() if any(k in ln for k in ("Uncaught", "chromium", "CONSOLE", "AndroidRuntime"))]
print("\n".join(lines[-8:]) if lines else "no JS/runtime errors in logcat tail")
