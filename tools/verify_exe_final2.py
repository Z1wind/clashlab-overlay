# -*- coding: utf-8 -*-
import os, re, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import ImageGrab
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
LOG = os.path.join(ROOT, "out", "overlay", "overlay.log")
subprocess.run(["powershell", "-NoProfile", "-Command",
                "Get-Process ClashOverlay -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue"],
               cwd=ROOT, capture_output=True, timeout=30)
time.sleep(2)
before = sum(1 for _ in open(LOG, "r", encoding="utf-8", errors="replace"))
subprocess.Popen([os.path.join(ROOT, "dist", "ClashOverlay.exe"), "--show", "--mode", "PANEL",
                  "--always-on-top", "--allow-primary"], cwd=ROOT,
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(8)
lines = open(LOG, "r", encoding="utf-8", errors="replace").readlines()[before:]
txt = "".join(lines)
print("new log lines:", len(lines), "| draw errors:", txt.count("draw_panel error") + txt.count("draw frame error"))
m = re.search(r"rect=\((\d+),(\d+),(\d+)x(\d+)\)", txt)
print("rect:", m.group(0) if m else "none")
print("tail:", [l.strip()[:100] for l in lines[-4:]])
if m:
    x, y, w, h = [int(v) for v in m.groups()]
    img = ImageGrab.grab(bbox=(x, y, x + w, y + h), all_screens=True)
    p = os.path.join(ROOT, "out", "live", "exe_panel_final.png")
    img.save(p)
    print("saved", p, img.size)
print("proc count:", subprocess.run(["powershell", "-NoProfile", "-Command",
      "(Get-Process ClashOverlay -ErrorAction SilentlyContinue | Measure-Object).Count"],
      capture_output=True, text=True).stdout.strip())
