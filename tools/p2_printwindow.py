# -*- coding: utf-8 -*-
"""P2-3：实机 PrintWindow 抓帧 + detect_boundary 真实置信。"""
import os, sys, json, time
import numpy as np, cv2
import win32gui
sys.path.insert(0, r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat")
from clashlab.overlay.runtime import _grab_window_frame
from clashlab import vision

BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "out", "overlay", "_p2")
os.makedirs(OUT, exist_ok=True)


def find_render():
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
    cand = [k for k in kids if "Render" in k[1] or "TheRender" in k[2]]
    return cand[0] if cand else None


kid = find_render()
print("render window:", kid)
hwnd = kid[0]
frame = _grab_window_frame(hwnd)
res = {"hwnd": hwnd, "rect": kid[3]}
if frame is None:
    res["error"] = "PrintWindow returned None"
    print("frame None")
else:
    h, w = frame.shape[:2]
    res.update({"shape": [int(h), int(w)], "mean_bgr": [float(x) for x in frame.reshape(-1, 3).mean(0)],
                "std": float(frame.std()), "nonblack_ratio": float((frame.max(2) > 8).mean())})
    cv2.imencode(".png", frame)[1].tofile(os.path.join(OUT, "printwindow_frame.png"))
    calib, meta = vision.detect_boundary(frame)
    assess = vision.boundary_assessment(calib, meta)
    res["detect_boundary"] = {"calib": calib is not None, "meta": meta, "assessment": assess}
json.dump(res, open(os.path.join(OUT, "printwindow_report.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "detect_boundary"}, ensure_ascii=False))
if "detect_boundary" in res:
    print("detect:", json.dumps(res["detect_boundary"], ensure_ascii=False)[:600])
