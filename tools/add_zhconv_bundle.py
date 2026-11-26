# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
# build script hiddenimport zhconv
p = os.path.join(BASE, "build_overlay.ps1")
t = open(p, encoding="ascii", errors="ignore").read()
if "zhconv" not in t:
    anchor = "    --hidden-import clashlab.cocapi " + BT
    t = t.replace(anchor, anchor + "\r\n    --hidden-import zhconv " + BT, 1)
    open(p, "w", encoding="ascii", newline="").write(t)
    print("build zhconv added")
# spec
p2 = os.path.join(BASE, "ClashOverlay.spec")
t2 = open(p2, encoding="utf-8").read()
t2 = t2.replace("'rapidocr_onnxruntime', 'onnxruntime', 'onnxruntime.capi._pybind_state']",
                "'rapidocr_onnxruntime', 'onnxruntime', 'onnxruntime.capi._pybind_state', 'zhconv']")
open(p2, "w", encoding="utf-8", newline="\n").write(t2)
# requirements
p3 = os.path.join(BASE, "requirements.txt")
t3 = open(p3, encoding="utf-8").read()
if "zhconv" not in t3:
    t3 = t3.rstrip() + "\nzhconv>=1.4\n"
    open(p3, "w", encoding="utf-8", newline="\n").write(t3)
    print("requirements zhconv added")
