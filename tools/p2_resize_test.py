# -*- coding: utf-8 -*-
"""P2-2：改雷电窗口大小（>10%）后，覆盖层是否自动跟随客户区并重建标定。"""
import os, sys, time, json, subprocess
import win32gui, win32con
from PIL import ImageGrab

BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "out", "overlay", "_p2")
PY = r"D:\Python313\python.exe"


def render_rect():
    h = win32gui.FindWindow("LDPlayerMainFrame", None)
    kids = []
    def walk(hwnd):
        c = None
        while True:
            c = win32gui.FindWindowEx(hwnd, c, None, None)
            if not c:
                break
            kids.append((c, win32gui.GetClassName(c), win32gui.GetWindowText(c), win32gui.GetWindowRect(c)))
            walk(c)
    walk(h)
    r = [k for k in kids if "Render" in k[1] or "TheRender" in k[2]]
    return h, r[0][3] if r else None


def main():
    h, r0 = render_rect()
    res = {"before": {"main": win32gui.GetWindowRect(h), "render": r0}}
    # 缩到约 80%（client 1280x720 -> ~1024x576，变化 >10%）
    wr = win32gui.GetWindowRect(h)
    w, hh = wr[2] - wr[0], wr[3] - wr[1]
    win32gui.SetWindowPos(h, None, wr[0], wr[1], int(w * 0.8), int(hh * 0.8), win32con.SWP_SHOWWINDOW)
    time.sleep(1.5)
    h2, r1 = render_rect()
    res["after_resize"] = {"main": win32gui.GetWindowRect(h2), "render": r1}
    # 起覆盖层
    p = subprocess.Popen([PY, "-W", "ignore", os.path.join(BASE, "run_overlay.py"), "--show", "--mode", "HUD",
                          "--always-on-top", "--allow-primary", "--run-seconds", "10"], cwd=BASE,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    time.sleep(5)
    ImageGrab.grab().save(os.path.join(OUT, "resize_small.png"))
    time.sleep(2)
    # 运行中再放大回去
    win32gui.SetWindowPos(h2, None, wr[0], wr[1], w, hh, win32con.SWP_SHOWWINDOW)
    time.sleep(6)
    ImageGrab.grab().save(os.path.join(OUT, "resize_back.png"))
    try:
        out, _ = p.communicate(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill(); out, _ = p.communicate()
    open(os.path.join(OUT, "resize_stdout.txt"), "wb").write(out or b"")
    h3, r2 = render_rect()
    res["final"] = {"main": win32gui.GetWindowRect(h3), "render": r2}
    json.dump(res, open(os.path.join(OUT, "resize_geom.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False))
    print("exit", p.returncode)


main()
