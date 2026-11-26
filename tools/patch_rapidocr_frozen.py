# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)

# 1) ocr_screen: 冻结环境下给 rapidocr 插件子包建别名
p = os.path.join(BASE, "clashlab", "ocr_screen.py")
t = open(p, encoding="utf-8").read()
if "_alias_plugins" not in t:
    t = t.replace('''def ocr_lines(img_bgr, crop=TOP_CROP, scale=3):''',
'''def _alias_plugins():
    """PyInstaller 冻结后 rapidocr 用 importlib.import_module("ch_ppocr_v3_det") 这种
    顶层名找插件；把子包别名注册进 sys.modules，源码运行与冻结运行都适用。"""
    import importlib
    import sys
    try:
        import rapidocr_onnxruntime as _r
    except Exception:
        return
    for name in ("ch_ppocr_v3_det", "ch_ppocr_v3_rec", "ch_ppocr_v2_cls"):
        if name in sys.modules:
            continue
        try:
            sys.modules[name] = importlib.import_module(_r.__name__ + "." + name)
        except Exception:
            pass


def ocr_lines(img_bgr, crop=TOP_CROP, scale=3):''')
    t = t.replace('''    from rapidocr_onnxruntime import RapidOCR  # 延迟导入：没装也能 import 本模块
    import cv2''',
'''    from rapidocr_onnxruntime import RapidOCR  # 延迟导入：没装也能 import 本模块
    import cv2
    _alias_plugins()''')
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("ocr_screen alias patch ok")

# 2) build_overlay.ps1 / debug 脚本加 collect-submodules
p2 = os.path.join(BASE, "build_overlay.ps1")
t2 = open(p2, encoding="ascii", errors="ignore").read()
if "--collect-submodules rapidocr_onnxruntime" not in t2:
    anchor = "    --collect-data rapidocr_onnxruntime " + BT
    add = ("\r\n    --collect-submodules rapidocr_onnxruntime " + BT +
           "\r\n    --collect-submodules onnxruntime " + BT)
    t2 = t2.replace(anchor, anchor + add, 1)
    open(p2, "w", encoding="ascii", newline="").write(t2)
    print("build script submodules added")

p3 = os.path.join(BASE, "tools", "build_debug.ps1")
t3 = open(p3, encoding="utf-8").read()
t3 = t3.replace("'--collect-data','rapidocr_onnxruntime','--collect-binaries','onnxruntime',",
                "'--collect-data','rapidocr_onnxruntime','--collect-binaries','onnxruntime',\n  '--collect-submodules','rapidocr_onnxruntime','--collect-submodules','onnxruntime',")
open(p3, "w", encoding="utf-8", newline="\n").write(t3)
print("debug script submodules added")
