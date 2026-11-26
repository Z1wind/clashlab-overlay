# -*- coding: utf-8 -*-
"""给 import_base.py 加「四角模型兜底」。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "import_base.py")
t = open(p, encoding="utf-8").read()
if "quad_model" in t:
    print("already patched"); raise SystemExit
old = """    calib, meta = calib_mod.detect_village_quad(frame, grid_n=44)
    if calib is None:"""
new = """    calib, meta = calib_mod.detect_village_quad(frame, grid_n=44)
    # 兜底：草地检测失败时用四角回归模型（存在 checkpoint 才用）
    if calib is None:
        try:
            from clashlab import quad_model as _qm
            _m = _qm.load_model()
            _q = _m.predict(frame)
            calib = calib_mod.Calib.from_quad(__import__("numpy").array(_q, dtype=__import__("numpy").float32), n=44)
            meta = {"method": "quad-model", "quad": [[float(x), float(y)] for x, y in _q]}
            print("草地检测失败，使用四角模型兜底")
        except Exception as _e:
            print("四角模型兜底不可用：%s" % str(_e)[:80])
    if calib is None:"""
if old in t:
    t = t.replace(old, new)
    open(p, "w", encoding="utf-8", newline=chr(10)).write(t)
    print("import_base patched")
else:
    print("anchor miss")
