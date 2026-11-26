# -*- coding: utf-8 -*-
"""实机观察：每 2s 抓一次游戏窗口，OCR 左上信息；发现对手名字就调 API 并落盘。
只读屏幕，不点击、不注入。"""
import json, os, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat")
import win32gui, win32ui, win32con
from PIL import Image
import numpy as np, cv2
from clashlab import ocr_screen, cocapi

HWND = 2097582
OUT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\live"
os.makedirs(OUT, exist_ok=True)
BAD = ("防守", "进攻", "部落冲突", "挂机助手", "小鹅", "雷电", "设置", "观战", "结束", "胜利", "失败")

def capture():
    left, top, right, bot = win32gui.GetWindowRect(HWND)
    w, h = right - left, bot - top
    hwndDC = win32gui.GetWindowDC(HWND)
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()
    bmp = win32ui.CreateBitmap()
    bmp.CreateCompatibleBitmap(mfcDC, w, h)
    saveDC.SelectObject(bmp)
    saveDC.BitBlt((0, 0), (w, h), mfcDC, (0, 0), win32con.SRCCOPY)
    path = os.path.join(OUT, "_frame.bmp")
    bmp.SaveBitmapFile(saveDC, path)
    win32gui.DeleteObject(bmp.GetHandle()); saveDC.DeleteDC(); mfcDC.DeleteDC(); win32gui.ReleaseDC(HWND, hwndDC)
    im = Image.open(path).convert("RGB")
    return np.array(im)[:, :, ::-1].copy()  # BGR

start = time.time()
last = ""
while time.time() - start < 180:
    try:
        img = capture()
    except Exception as e:
        print("capture fail", e); time.sleep(2); continue
    game = img[30:, :, :]  # 去掉标题栏
    try:
        got = ocr_screen.read_opponent(game)
    except Exception as e:
        print("ocr fail", str(e)[:80]); time.sleep(2); continue
    lines = [l["text"] for l in got.get("lines") or []]
    if lines and lines != last:
        print("[ocr]", lines, flush=True)
        last = lines
    cand = None
    for t in lines:
        t = t.strip()
        if len(t) >= 3 and not any(b in t for b in BAD) and not t.startswith("离"):
            cand = t
            break
    if cand and got.get("clan"):
        try:
            res = cocapi.resolve_opponent(cand, got.get("clan"), fresh=True, ocr_level=got.get("level"))
        except Exception as e:
            print("api fail", str(e)[:100]); time.sleep(2); continue
        p = (res.get("player") or {})
        if p.get("tag"):
            payload = {"ocr": got, "api": res, "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
            path = os.path.join(OUT, "enemy_live.json")
            json.dump(payload, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            Image.fromarray(img[:, :, ::-1]).save(os.path.join(OUT, "enemy_live_frame.png"))
            print("[HIT]", p.get("name"), p.get("tag"), "TH", p.get("th"), "->", path, flush=True)
            break
    time.sleep(2)
print("watcher done", flush=True)
