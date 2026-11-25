# -*- coding: utf-8 -*-
"""多轮实机测试：HUD/PANEL × 有/无布局 × 改窗口大小，逐轮记录退出码/日志/截图。"""
import os, sys, json, time, subprocess, shutil
from PIL import ImageGrab

BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
QA = os.path.join(BASE, "out", "qa")
os.makedirs(QA, exist_ok=True)
PY = r"D:\Python313\python.exe"
LAY = os.path.join(BASE, "layouts", "layout_current.json")
SRC = os.path.join(BASE, "bases", "th16", "03", "layout.json")

def set_layout(on):
    if on:
        shutil.copy2(SRC, LAY)
    else:
        if os.path.exists(LAY):
            os.remove(LAY)

def run_overlay(tag, args, seconds, resize_mid=False):
    log = []
    p = subprocess.Popen([PY, "-W", "ignore", os.path.join(BASE, "run_overlay.py")] + args,
                         cwd=BASE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    t0 = time.time()
    shot_ok = False
    shot = os.path.join(QA, "soak_%s.png" % tag)
    resized = False
    while time.time() - t0 < seconds:
        time.sleep(1.0)
        if resize_mid and not resized and time.time() - t0 > 3.0:
            try:
                import win32gui, win32con
                h = win32gui.FindWindow("LDPlayerMainFrame", None)
                r = win32gui.GetWindowRect(h)
                w, hh = r[2] - r[0], r[3] - r[1]
                win32gui.SetWindowPos(h, None, r[0], r[1], int(w * 0.8), int(hh * 0.8), win32con.SWP_SHOWWINDOW)
                time.sleep(2.0)
                win32gui.SetWindowPos(h, None, r[0], r[1], w, hh, win32con.SWP_SHOWWINDOW)
                resized = True
            except Exception as e:
                log.append("resize_err:%r" % (e,))
        if not shot_ok and time.time() - t0 > 4.0:
            try:
                ImageGrab.grab().save(shot)
                shot_ok = True
            except Exception:
                pass
    try:
        out, _ = p.communicate(timeout=25)
    except subprocess.TimeoutExpired:
        p.kill(); out, _ = p.communicate()
    text = (out or b"").decode("utf-8", "ignore")
    if not shot_ok:
        try:
            ImageGrab.grab().save(shot)
        except Exception:
            pass
    lines = text.splitlines()
    return {"tag": tag, "exit": p.returncode, "lines": len(lines),
            "traceback": sum(1 for l in lines if "Traceback" in l),
            "errors": sum(1 for l in lines if ("error" in l.lower() or "exception" in l.lower()) and "error" not in ("",)),
            "has_end": any("runtime end" in l for l in lines),
            "has_rect": any("rect=" in l for l in lines),
            "shot": os.path.basename(shot) if os.path.exists(shot) else None,
            "shot_bytes": os.path.getsize(shot) if os.path.exists(shot) else 0,
            "extra": log}

def main():
    results = []
    try:
        # R1/R2 HUD 无布局/有布局
        for tag, lay in (("r1_hud_nolayout", False), ("r2_hud_layout", True)):
            set_layout(lay)
            results.append(run_overlay(tag, ["--show", "--mode", "HUD", "--always-on-top",
                                             "--allow-primary", "--run-seconds", "7"], 9))
        # R3/R4 PANEL 有布局/无布局
        for tag, lay in (("r3_panel_layout", True), ("r4_panel_nolayout", False)):
            set_layout(lay)
            results.append(run_overlay(tag, ["--show", "--mode", "PANEL", "--always-on-top",
                                             "--allow-primary", "--run-seconds", "7"], 9))
        # R5 HUD 中途改窗口大小（自动重标定）
        set_layout(True)
        results.append(run_overlay("r5_hud_resize", ["--show", "--mode", "HUD", "--always-on-top",
                                                     "--allow-primary", "--run-seconds", "12"], 14, resize_mid=True))
        # R6 exe 自检 + R7 exe HUD
        exe = os.path.join(BASE, "dist", "ClashOverlay.exe")
        p = subprocess.run([exe, "--seconds", "6", "--no-show"], cwd=BASE, capture_output=True, timeout=120)
        results.append({"tag": "r6_exe_selfcheck", "exit": p.returncode})
        q = subprocess.Popen([exe, "--show", "--mode", "HUD", "--always-on-top", "--allow-primary",
                              "--run-seconds", "7"], cwd=BASE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        t0 = time.time()
        shot = os.path.join(QA, "soak_r7_exe_hud.png")
        while time.time() - t0 < 9:
            time.sleep(1.0)
            if time.time() - t0 > 4 and not os.path.exists(shot):
                try:
                    ImageGrab.grab().save(shot)
                except Exception:
                    pass
        try:
            out, _ = q.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            q.kill(); out, _ = q.communicate()
        results.append({"tag": "r7_exe_hud", "exit": q.returncode,
                        "shot_bytes": os.path.getsize(shot) if os.path.exists(shot) else 0})
    finally:
        set_layout(False)
    ok = 0
    for r in results:
        if r.get("tag") == "r6_exe_selfcheck":
            good = r.get("exit") == 0  # 自检模式不截图、无 runtime end，仅看退出码
        else:
            good = (r.get("exit") == 0 and r.get("traceback", 0) == 0
                    and r.get("has_end", True) and r.get("shot_bytes", 0) > 10000)
        r["pass"] = good
        ok += good
    json.dump(results, open(os.path.join(QA, "soak_report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("PASS %d/%d" % (ok, len(results)))
    for r in results:
        print(json.dumps(r, ensure_ascii=False))

main()
