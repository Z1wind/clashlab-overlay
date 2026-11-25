# -*- coding: utf-8 -*-
# Step1: 循环双指外扩至最大档，帧差 MAD 判到顶。纯输入+截图，不读内存。
import subprocess, time, os, sys
import numpy as np, cv2

ADB = r"E:\leidian\LDPlayer9\adb.exe"
OUT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay"
SEQ = os.path.join(OUT, "pinch_seq")
os.makedirs(SEQ, exist_ok=True)

def sh(args, binary=False):
    cp = subprocess.run([ADB] + args, capture_output=True, timeout=30)
    return cp.stdout if binary else cp.stdout.decode("utf-8", "ignore")

def frame():
    raw = sh(["exec-out", "screencap", "-p"], binary=True)
    img = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    return img

def save(img, path):
    cv2.imencode(".png", img)[1].tofile(path)

def mad(a, b, box=(300,150,980,570)):
    x1,y1,x2,y2 = box
    ga = cv2.cvtColor(a[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY).astype(np.float32)
    gb = cv2.cvtColor(b[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY).astype(np.float32)
    return float(np.mean(np.abs(ga-gb)))

prev = frame()
save(prev, os.path.join(SEQ, "b00.png"))
plateau = 0
for batch in range(1, 16):
    sh(["shell", "sh", "/data/local/tmp/pinch.sh", "14", "10"])
    time.sleep(1.8)
    cur = frame()
    m = mad(prev, cur)
    save(cur, os.path.join(SEQ, f"b{batch:02d}.png"))
    print(f"batch {batch:02d} MAD={m:.2f}")
    prev = cur
    if m < 1.5:
        plateau += 1
        if plateau >= 2:
            print("PLATEAU reached at batch", batch)
            break
    else:
        plateau = 0
save(cur, os.path.join(OUT, "v6_zoom_max_raw.png"))
print("saved v6_zoom_max_raw.png", cur.shape)
