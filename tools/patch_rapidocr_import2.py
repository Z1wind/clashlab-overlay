# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"

# 1) ocr_screen: 在构造 RapidOCR 前临时重定向 importlib 的裸插件名
p = os.path.join(BASE, "clashlab", "ocr_screen.py")
t = open(p, encoding="utf-8").read()
if "_patch_rapidocr_imports" not in t:
    t = t.replace('''    from rapidocr_onnxruntime import RapidOCR  # 延迟导入：没装也能 import 本模块
    import cv2
    _alias_plugins()''',
'''    from rapidocr_onnxruntime import RapidOCR  # 延迟导入：没装也能 import 本模块
    import cv2
    _alias_plugins()
    import importlib as _il
    import rapidocr_onnxruntime.rapid_ocr_api as _rapi
    _orig_import = _il.import_module
    _plugins = ("ch_ppocr_v3_det", "ch_ppocr_v3_rec", "ch_ppocr_v2_cls")

    def _patched(name, package=None):
        if name in _plugins:
            name = "rapidocr_onnxruntime." + name
        return _orig_import(name, package) if package is not None else _orig_import(name)

    _il.import_module = _patched
    try:
        engine = RapidOCR()
    finally:
        _il.import_module = _orig_import''')
    t = t.replace('''    engine = RapidOCR()
    res, _ = engine(sub)''', '''    res, _ = engine(sub)''')
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("import redirect patched")

# 2) debug build script: 不要 Stop（PyInstaller stderr 会被当错误中止）
p2 = os.path.join(BASE, "tools", "build_debug.ps1")
t2 = open(p2, encoding="utf-8").read()
t2 = t2.replace("$ErrorActionPreference = 'Stop'", "$ErrorActionPreference = 'Continue'")
t2 = t2.replace("& $py -m PyInstaller @a *> 'out\\logs\\build_debug.log'",
                "cmd /c \"\\\"$py\\\" -m PyInstaller @a > out\\logs\\build_debug.log 2>&1\"")
open(p2, "w", encoding="utf-8", newline="\n").write(t2)
print("debug script patched")
