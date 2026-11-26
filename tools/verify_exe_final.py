# -*- coding: utf-8 -*-
import os, re, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import ImageGrab
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
LOG = os.path.join(ROOT, "out", "overlay", "overlay.log")
before = sum(1 for _ in open(LOG, "r", encoding="utf-8", errors="replace"))
subprocess.run(["powershell", "-NoProfile", "-Command",
                "Start-Process -FilePath (Resolve-Path 'dist\\ClashOverlay.exe') -ArgumentList '--show','--mode','PANEL','--always-on-top','--allow-primary' -WorkingDirectory (Get-Location).Path"],
               cwd=ROOT, capture_output=True, timeout=30)
time.sleep(6)
lines = open(LOG, "r", encoding="utf-8", errors="replace").readlines()[before:]
txt = "".join(lines)
print("new log lines:", len(lines), "| draw errors:", txt.count("draw_panel error") + txt.count("draw frame error"))
m = re.search(r"rect=\((\d+),(\d+),(\d+)x(\d+)\)", txt)
print("rect:", m.group(0) if m else "none")
if m:
    x, y, w, h = [int(v) for v in m.groups()]
    img = ImageGrab.grab(bbox=(x, y, x + w, y + h), all_screens=True)
    p = os.path.join(ROOT, "out", "live", "exe_panel_final.png")
    img.save(p)
    print("saved", p, img.size)
subprocess.run(["powershell", "-NoProfile", "-Command", "Get-Process ClashOverlay | Select-Object Id,Responding | Format-Table -AutoSize | Out-String"],
               cwd=ROOT, capture_output=True, timeout=30)
print("processes:", subprocess.run(["powershell", "-NoProfile", "-Command",
      "(Get-Process ClashOverlay -ErrorAction SilentlyContinue | Measure-Object).Count"], capture_output=True, text=True).stdout.strip())
