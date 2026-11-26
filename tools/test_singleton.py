# -*- coding: utf-8 -*-
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import win32gui
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
LOG = os.path.join(ROOT, "out", "overlay", "overlay.log")
before = sum(1 for _ in open(LOG, "r", encoding="utf-8", errors="replace"))
subprocess.Popen([os.path.join(ROOT, "dist", "ClashOverlay.exe"), "--show", "--mode", "PANEL",
                  "--allow-primary"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(5)
lines = open(LOG, "r", encoding="utf-8", errors="replace").readlines()[before:]
hits = [l.strip()[:110] for l in lines if "another ClashLab" in l or "singleton" in l]
win = []
def cb(h, _):
    if win32gui.IsWindowVisible(h) and win32gui.GetClassName(h) == "GLFW30":
        l, t, r, b = win32gui.GetWindowRect(h)
        win.append((r - l, b - t))
    return True
win32gui.EnumWindows(cb, None)
print("second launch log:", hits)
print("overlay windows now:", win)
proc = subprocess.run(["powershell", "-NoProfile", "-Command",
                       "(Get-Process ClashOverlay -ErrorAction SilentlyContinue | Measure-Object).Count"],
                      capture_output=True, text=True).stdout.strip()
print("ClashOverlay processes:", proc)
