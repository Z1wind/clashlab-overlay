# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)

p = os.path.join(BASE, "build_overlay.ps1")
t = open(p, encoding="ascii", errors="ignore").read()
if "rapidocr_onnxruntime" not in t:
    anchor1 = "    --collect-binaries imgui_bundle " + BT
    add1 = ("    --collect-data rapidocr_onnxruntime " + BT + "\r\n" +
            "    --collect-binaries onnxruntime " + BT + "\r\n")
    t = t.replace(anchor1, anchor1 + "\r\n" + add1.rstrip("\r\n"), 1)
    anchor2 = "    --hidden-import numpy " + BT
    add2 = ("\r\n    --hidden-import rapidocr_onnxruntime " + BT +
            "\r\n    --hidden-import onnxruntime " + BT +
            "\r\n    --hidden-import onnxruntime.capi._pybind_state " + BT +
            "\r\n    --hidden-import clashlab.ocr_screen " + BT +
            "\r\n    --hidden-import clashlab.cocapi " + BT)
    t = t.replace(anchor2, anchor2 + add2, 1)
    open(p, "w", encoding="ascii", newline="").write(t)
    print("build script patched")

p2 = os.path.join(BASE, "ClashOverlay.spec")
t2 = open(p2, encoding="utf-8").read()
if "rapidocr_onnxruntime" not in t2:
    t2 = t2.replace("binaries += collect_dynamic_libs('imgui_bundle')",
                    "binaries += collect_dynamic_libs('imgui_bundle')\n"
                    "datas += collect_data_files('rapidocr_onnxruntime')\n"
                    "binaries += collect_dynamic_libs('onnxruntime')")
    t2 = t2.replace("'clashlab.vision', 'cv2', 'numpy']",
                    "'clashlab.vision', 'clashlab.ocr_screen', 'clashlab.cocapi', 'cv2', 'numpy',\n"
                    "                   'rapidocr_onnxruntime', 'onnxruntime', 'onnxruntime.capi._pybind_state']")
    open(p2, "w", encoding="utf-8", newline="\n").write(t2)
    print("spec patched")
