# -*- coding: utf-8 -*-
"""自动侦察抓图流水线：战争地图 → 敌军 → 逐个基地 → 侦察 → 截图 → 返回。

用法：
    python tools/war_scout_capture.py --max 8 --out out/live/war1080
"""
import argparse, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ADB = r"E:\leidian\LDPlayer9\adb.exe"; DEV = "emulator-5554"
_E = None

def sh(*a, timeout=90):
    return subprocess.run(list(a), capture_output=True, text=True, timeout=timeout)

def screencap(path):
    sh(ADB, "-s", DEV, "shell", "screencap", "-p", "/sdcard/s.png")
    sh(ADB, "-s", DEV, "pull", "/sdcard/s.png", path)
    img = cv2.imdecode(np.fromfile(path, np.uint8), cv2.IMREAD_COLOR)
    return img

def ocr(img):
    global _E
    if _E is None:
        _E = RapidOCR()
    res, _ = _E(img)
    return [(box, str(txt)) for box, txt, _s in (res or [])]

def find(img, keyword, min_y=None):
    for box, txt in ocr(img):
        if keyword in txt:
            xs = [p[0] for p in box]; ys = [p[1] for p in box]
            y = sum(ys) / 4
            if min_y is not None and y < min_y:
                continue
            return int(sum(xs) / 4), int(y), txt
    return None

def tap(x, y, wait=2.5):
    sh(ADB, "-s", DEV, "shell", "input", "tap", str(int(x)), str(int(y)))
    time.sleep(wait)

def back(wait=1.5):
    sh(ADB, "-s", DEV, "shell", "input", "keyevent", "4")
    time.sleep(wait)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=8)
    ap.add_argument("--out", default=os.path.join(BASE, "out", "live", "war1080"))
    ap.add_argument("--start", type=int, default=1)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    cur = os.path.join(a.out, "_cur.png")
    img = screencap(cur)
    print("screen:", None if img is None else img.shape[:2], flush=True)
    # 断线重连处理（重载需要时间，多等）
    for _ in range(4):
        img = screencap(cur)
        hit = find(img, "重新载入")
        if hit:
            print("reconnect dialog -> tap", flush=True)
            tap(hit[0], hit[1], 20)
            continue
        break
    # 确保在战争地图（OCR 状态机，不用 back 以免触发退出确认）
    for _ in range(8):
        img = screencap(cur)
        if find(img, "确定退出"):
            hit = find(img, "取消")
            if hit:
                tap(hit[0], hit[1], 1.5)
            continue
        if find(img, "战争地图"):
            hit = find(img, "战争地图")
            tap(hit[0], hit[1], 2.5)
            continue
        if find(img, "敌军") or find(img, "我军") or find(img, "准备日") or find(img, "战斗日"):
            break
        tap(75, 650, 2.5)
    img = screencap(cur)
    if find(img, "敌军"):
        hit = find(img, "敌军")
        tap(hit[0], hit[1], 3)
        img = screencap(cur)
    # 逐基地：OCR 名字形如 "1." "2." …
    shots = 0
    for i in range(a.start, a.start + a.max):
        img = screencap(cur)
        _sw = find(img, "敌军") or find(img, "我军")
        if _sw:
            tap(_sw[0], _sw[1], 3)
            img = screencap(cur)
        import re
        hits = []
        for box, txt in ocr(img):
            m = re.match(r"\s*([0-9Il]{1,2})\s*[\.\,\s]", txt.strip())
            if not m:
                continue
            num = m.group(1).replace("I", "1").replace("l", "1")
            if num.isdigit() and int(num) == i:
                hits.append((box, txt))
        if not hits:
            print("base", i, "not found on map", flush=True)
            continue
        box, txt = hits[0]
        xs = [p[0] for p in box]; ys = [p[1] for p in box]
        bx, by = int(sum(xs) / 4), int(sum(ys) / 4)
        tap(bx, by + 70, 2.5)          # 点名字下方的基地
        img = screencap(cur)
        hit = find(img, "侦察")
        if not hit:
            print("base", i, "no scout button; back", flush=True)
            back()
            continue
        tap(hit[0], hit[1], 5)
        base_shot = os.path.join(a.out, "base_%02d_%s.png" % (i, time.strftime("%H%M%S")))
        img2 = screencap(base_shot)
        print("captured", base_shot, None if img2 is None else img2.shape[:2], flush=True)
        shots += 1
        hit = find(img2, "战争地图")
        if hit:
            tap(hit[0], hit[1], 2.5)
        else:
            back(1.5)
    print("DONE shots", shots, flush=True)

if __name__ == "__main__":
    main()
