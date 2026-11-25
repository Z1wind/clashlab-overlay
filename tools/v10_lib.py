# -*- coding: utf-8 -*-
# v10_lib.py — 全阵采集公共库（只读抓帧/ORB位移/tile_px/客户区现算）。新文件，不改旧模块。
import subprocess, os, json, time, cv2, numpy as np

ADB = r"E:\leidian\LDPlayer9\adb.exe"
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
FULL = os.path.join(ROOT, "out", "overlay", "full")
RAW = os.path.join(FULL, "raw")
os.makedirs(RAW, exist_ok=True)

# 内容裁口（去掉顶部奖励条/右侧资源轨/底部按钮条/左侧工具栏），采集前可再校准
TRIM = (150, 75, 1015, 612)

def sh(a, binary=False):
    cp = subprocess.run([ADB] + a, capture_output=True, timeout=30)
    return cp.stdout if binary else cp.stdout.decode("utf-8", "ignore")

def grab():
    raw = sh(["exec-out", "screencap", "-p"], binary=True)
    return cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)

def trim(im):
    x1, y1, x2, y2 = TRIM
    return im[y1:y2, x1:x2]

_orb = cv2.ORB_create(1500)

def orb_shift(a, b, tol=15):
    """a=旧帧, b=新帧（裁口灰度）；返回 (dx,dy) b相对a中位位移, inliers, good数；失败 None。"""
    ga = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY) if a.ndim == 3 else a
    gb = cv2.cvtColor(b, cv2.COLOR_BGR2GRAY) if b.ndim == 3 else b
    ka, da = _orb.detectAndCompute(ga, None)
    kb, db = _orb.detectAndCompute(gb, None)
    if da is None or db is None or len(ka) < 10 or len(kb) < 10:
        return None, 0, 0
    bf = cv2.BFMatcher(cv2.NORM_HAMMING)
    knn = bf.knnMatch(da, db, k=2)
    good = [m for m, n in knn if m.distance < 0.75 * n.distance]
    if len(good) < 8:
        return None, 0, len(good)
    pa = np.float32([ka[m.queryIdx].pt for m in good])
    pb = np.float32([kb[m.trainIdx].pt for m in good])
    d = pb - pa
    mx, my = np.median(d, axis=0)
    inn = np.linalg.norm(d - [mx, my], axis=1) < tol
    if inn.sum() >= 6:
        mx, my = np.median(d[inn], axis=0)
    return (float(mx), float(my)), int(inn.sum()), len(good)

def tile_px_of(im):
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from v6_tile_px import measure_tile_px
    return measure_tile_px(trim(im) if im.shape[:2] != trim(im).shape[:2] else im)

def client_rect():
    import win32gui
    main = []
    win32gui.EnumWindows(lambda h, _: main.append(h) if win32gui.GetClassName(h) == "LDPlayerMainFrame" and win32gui.IsWindowVisible(h) else None, None)
    if not main:
        return None
    h = main[0]
    out = {"main": None, "render": None}
    cr = win32gui.GetClientRect(h); pt = win32gui.ClientToScreen(h, (0, 0))
    out["main"] = {"hwnd": int(h), "origin": list(pt), "size": [cr[2], cr[3]]}
    kids = []
    def collect(k):
        sub = []
        win32gui.EnumChildWindows(k, lambda x, _: sub.append(x), None)
        for x in sub:
            kids.append(x); collect(x)
    collect(h)
    for k in kids:
        if win32gui.IsWindowVisible(k) and win32gui.GetClassName(k) == "RenderWindow":
            r = win32gui.GetClientRect(k); p = win32gui.ClientToScreen(k, (0, 0))
            out["render"] = {"hwnd": int(k), "origin": list(p), "size": [r[2], r[3]]}
            break
    return out

def mad(a, b):
    ga = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY).astype(np.float32)
    gb = cv2.cvtColor(b, cv2.COLOR_BGR2GRAY).astype(np.float32)
    return float(np.mean(np.abs(ga - gb)))

LOG = os.path.join(FULL, "collect_log.json")

def load_log():
    if os.path.exists(LOG):
        return json.load(open(LOG, encoding="utf-8"))
    return {"blocks": [], "meta": {}}

def save_log(d):
    json.dump(d, open(LOG, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def save_png(im, path):
    cv2.imencode(".png", im)[1].tofile(path)
