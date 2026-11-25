# -*- coding: utf-8 -*-
# v10 探针：抓帧 + v6_tile_px 三判据 + ORB 对 zoom_L0 参考 + win32 客户区现算。只读不点。
import subprocess, time, os, sys, json, cv2, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v6_tile_px import measure_tile_px

ADB = r"E:\leidian\LDPlayer9\adb.exe"
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(ROOT, "out", "overlay", "full")
os.makedirs(OUT, exist_ok=True)

def sh(a, binary=False):
    cp = subprocess.run([ADB] + a, capture_output=True, timeout=30)
    return cp.stdout if binary else cp.stdout.decode("utf-8", "ignore")

def frame():
    raw = sh(["exec-out", "screencap", "-p"], binary=True)
    return cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)

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

im = frame()
h, w = im.shape[:2]
print("frame size:", w, h)

# 中央草地/建筑混合窗测 tile_px（避开顶部奖励条与底部按钮）
crop = im[90:600, 150:1130]
r = measure_tile_px(crop)
print("tile_px:", json.dumps(r, ensure_ascii=False))

# ORB 对 L0 参考
ref = cv2.imdecode(np.fromfile(os.path.join(ROOT, "out", "overlay", "ladder", "zoom_L0.png"), dtype=np.uint8), cv2.IMREAD_COLOR)
orb = cv2.ORB_create(1500)
ka, da = orb.detectAndCompute(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), None)
kb, db = orb.detectAndCompute(cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY), None)
n_inl = 0; shift = None
if da is not None and db is not None:
    bf = cv2.BFMatcher(cv2.NORM_HAMMING)
    good = [m for m, n in bf.knnMatch(da, db, k=2) if m.distance < 0.75 * n.distance]
    if len(good) >= 10:
        pa = np.float32([ka[m.queryIdx].pt for m in good]); pb = np.float32([kb[m.trainIdx].pt for m in good])
        d = pb - pa; mx, my = np.median(d, axis=0)
        inn = np.linalg.norm(d - [mx, my], axis=1) < 15
        n_inl = int(inn.sum()); shift = [round(float(mx), 1), round(float(my), 1)]
    print(f"ORB vs zoom_L0: good={len(good) if da is not None else 0} inl={n_inl} shift={shift}")

rect = client_rect()
print("client_rect:", json.dumps(rect, ensure_ascii=False))

cv2.imencode(".png", im)[1].tofile(os.path.join(OUT, "probe_full.png"))
json.dump({"frame_size": [w, h], "tile_px": r, "orb_vs_L0": {"inl": n_inl, "shift": shift},
           "client": rect, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")},
          open(os.path.join(OUT, "probe.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("saved probe_full.png")
