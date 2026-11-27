# -*- coding: utf-8 -*-
"""交付自测：exe 面板、四页切换、三语、HUD、单实例、日志错误。"""
import ctypes, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import ImageGrab
import win32gui
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EXE = os.path.join(ROOT, "dist", "ClashOverlay.exe")
LOG = os.path.join(ROOT, "out", "overlay", "overlay.log")
def kill():
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    "Get-Process ClashOverlay -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue; "
                    "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -like '*run_overlay.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"],
                   capture_output=True, timeout=25)
def windows():
    out = []
    def cb(h, _):
        if win32gui.IsWindowVisible(h) and win32gui.GetClassName(h) == "GLFW30":
            l, t, r, b = win32gui.GetWindowRect(h)
            out.append((h, l, t, r, b))
        return True
    win32gui.EnumWindows(cb, None)
    return out
def wait_panel(tries=15):
    for _ in range(tries):
        time.sleep(1)
        good = [w for w in windows() if abs((w[3] - w[1]) - 440) <= 12]
        if good:
            return good[0]
    return None
kill(); time.sleep(1)
before = sum(1 for _ in open(LOG, "r", encoding="utf-8", errors="replace"))
subprocess.Popen([EXE, "--show", "--mode", "PANEL", "--lang", "zh", "--allow-primary"],
                 cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
win = wait_panel()
print("panel:", win)
u = ctypes.windll.user32
if win:
    h, x0, y0, x1, y1 = win
    def click(px, py=25, times=2):
        for _ in range(times):
            u.SetCursorPos(int(x0 + px), int(y0 + py)); time.sleep(0.15)
            u.mouse_event(2, 0, 0, 0, 0); time.sleep(0.05); u.mouse_event(4, 0, 0, 0, 0)
            time.sleep(0.55)
    click(220, 620, 1)  # 激活
    for name, px in (("research", 52), ("layout", 132), ("capture", 212), ("settings", 292)):
        click(px)
        ImageGrab.grab(bbox=(x0, y0, x1, y1), all_screens=True).save(os.path.join(ROOT, "out", "live", "qa_%s.png" % name))
    print("panel pages captured")
    # 语言按钮：中(约 +341) 繁(+372) EN(+403)
    for name, px in (("zh", 341), ("hant", 372), ("en", 403)):
        click(px, 25, 1); time.sleep(0.8)
        ImageGrab.grab(bbox=(x0, y0, x1, y1), all_screens=True).save(os.path.join(ROOT, "out", "live", "qa_lang_%s.png" % name))
    print("language captures done")
    # 单实例
    subprocess.Popen([EXE, "--show", "--mode", "PANEL", "--allow-primary"], cwd=ROOT,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(4)
    lines = open(LOG, "r", encoding="utf-8", errors="replace").readlines()[before:]
    txt = "".join(lines)
    print("singleton log:", "another ClashLab" in txt)
    print("draw errors:", txt.count("draw_panel error") + txt.count("draw frame error"))
    print("windows after 2nd:", len(windows()))
kill(); time.sleep(1)
# HUD
subprocess.Popen([EXE, "--show", "--mode", "HUD", "--lang", "zh", "--always-on-top", "--allow-primary"],
                 cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
w = None
for _ in range(15):
    time.sleep(1)
    good = [x for x in windows() if (x[3] - x[1]) > 600]
    if good:
        w = good[0]; break
print("hud:", w)
if w:
    time.sleep(1)
    h, x0, y0, x1, y1 = w
    ImageGrab.grab(bbox=(x0, y0, x1, y1), all_screens=True).save(os.path.join(ROOT, "out", "live", "qa_hud.png"))
    print("hud captured", (x1 - x0, y1 - y0))
