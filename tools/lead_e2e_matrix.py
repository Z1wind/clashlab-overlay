# -*- coding: utf-8 -*-
"""Lead 侧实机矩阵（低风险，不改产品代码）：HUD+布局 / PANEL 无布局 / EXE 自检，截图与日志。"""
import os, shutil, subprocess, time
from PIL import ImageGrab
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
QA = os.path.join(BASE, "out", "qa_e2e")
os.makedirs(QA, exist_ok=True)
LAY = os.path.join(BASE, "layouts", "layout_current.json")
SRC = os.path.join(BASE, "bases", "th16", "03", "layout.json")
bak = LAY + ".lead_bak"
had = os.path.exists(LAY)
if had:
    shutil.copy2(LAY, bak)

def run(tag, args, seconds=8):
    p = subprocess.Popen([r"D:\Python313\python.exe", "-u", os.path.join(BASE, "run_overlay.py")] + args,
                         cwd=BASE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    t0 = time.time(); shot = os.path.join(QA, "lead_%s.png" % tag); saved = False
    while time.time() - t0 < seconds:
        time.sleep(1)
        if not saved and time.time() - t0 > 4:
            ImageGrab.grab().save(shot); saved = True
    try:
        out, _ = p.communicate(timeout=30)
    except subprocess.TimeoutExpired:
        p.kill(); out, _ = p.communicate()
    log = (out or b"").decode("utf-8", "ignore")
    tb = log.count("Traceback")
    fps = [ln for ln in log.splitlines() if "fps summary" in ln]
    return {"tag": tag, "exit": p.returncode, "traceback": tb, "fps": fps[-1][:120] if fps else "",
            "shot": os.path.basename(shot) if os.path.exists(shot) else None,
            "bytes": os.path.getsize(shot) if os.path.exists(shot) else 0}

try:
    shutil.copy2(SRC, LAY)
    rows = [run("hud_layout", ["--show", "--mode", "HUD", "--always-on-top", "--allow-primary", "--run-seconds", "7"])]
    os.remove(LAY)
    rows.append(run("panel_nolayout", ["--show", "--mode", "PANEL", "--always-on-top", "--allow-primary", "--run-seconds", "7"]))
finally:
    if os.path.exists(LAY):
        os.remove(LAY)
    if had:
        shutil.move(bak, LAY)

exe = os.path.join(BASE, "dist", "ClashOverlay.exe")
r = subprocess.run([exe, "--seconds", "6", "--no-show"], cwd=BASE, capture_output=True, timeout=120)
rows.append({"tag": "exe_selfcheck", "exit": r.returncode, "traceback": 0, "shot": None, "bytes": 0})
for row in rows:
    print(row)
