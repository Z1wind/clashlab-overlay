# -*- coding: utf-8 -*-
"""自动标注用 ADB 驱动：点击/截图/等待，内置「进攻按钮禁区」保护。"""
import subprocess, time, hashlib
import numpy as np, cv2

ADB = r"E:\leidian\LDPlayer9\adb.exe"
DEV = "emulator-5554"
DANGER_BOXES = [(430, 600, 700, 700), (740, 520, 920, 600)]


def sh(args, timeout=40):
    r = subprocess.run([ADB, "-s", DEV] + args, capture_output=True, timeout=timeout)
    return r.stdout, r.stderr


def tap(x, y, note=""):
    for x0, y0, x1, y1 in DANGER_BOXES:
        if x0 <= x <= x1 and y0 <= y <= y1:
            raise RuntimeError("拒绝点击危险区域 (%d,%d) %s" % (x, y, note))
    sh(["shell", "input", "tap", str(int(x)), str(int(y))])


def swipe(x0, y0, x1, y1, ms=400):
    sh(["shell", "input", "swipe", str(int(x0)), str(int(y0)), str(int(x1)), str(int(y1)), str(int(ms))])


def shot(path=None):
    out, _ = sh(["exec-out", "screencap", "-p"], timeout=60)
    if not out.startswith(b"\x89PNG"):
        raise RuntimeError("截图失败 %r" % out[:16])
    if path:
        with open(path, "wb") as f:
            f.write(out)
    return cv2.imdecode(np.frombuffer(out, np.uint8), cv2.IMREAD_COLOR)


def stable(timeout=90, interval=1.0, thresh=0.004):
    prev = shot()
    t0 = time.time()
    while time.time() - t0 < timeout:
        time.sleep(interval)
        cur = shot()
        d = float(np.mean(cv2.absdiff(prev, cur))) / 255.0
        if d < thresh:
            return cur, d
        prev = cur
    return prev, None


def digest(img):
    return hashlib.sha256(img.tobytes()).hexdigest()[:16]
