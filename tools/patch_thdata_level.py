# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "th_data.py")
t = open(p, encoding="utf-8").read()
old = 'def stats(name, th):\n    """按本数取数：优先该档精确条目；缺失回落“不高于该 TH 的最近档”并标 approx=True。'
# 用更稳的锚：函数定义 + docstring 首行
import re
m = re.search(r"def stats\(name, th\):\n", t)
if not m:
    print("sig anchor miss")
else:
    if "level=None" not in t:
        t = t.replace("def stats(name, th):", "def stats(name, th, level=None):", 1)
        # 在 return out 前插入缩放逻辑（最后一次出现）
        tail = '''    out = dict(entry)
    out["th"] = t
    out["approx"] = approx
    out["approx_from"] = from_th if approx else None
    out["unknown"] = unknown
    return out'''
        new_tail = '''    out = dict(entry)
    out["th"] = t
    out["approx"] = approx
    out["approx_from"] = from_th if approx else None
    out["unknown"] = unknown
    # 等级：显式给定则按曲线缩放 hp/dps（满级 = 原值），否则标记 level_estimated
    if level is not None:
        from . import levels as _levels
        _mx = int(out.get("level") or 0) or _levels.DEFAULT_MAX_LEVEL
        _sc = _levels.building_scale(int(level), _mx)
        out["hp"] = round(float(out.get("hp") or 0) * _sc["hp"], 3)
        out["dps"] = round(float(out.get("dps") or 0) * _sc["dps"], 3)
        out["level"] = int(level)
        out["level_max"] = _mx
        out["level_estimated"] = False
    else:
        out["level_estimated"] = True
    return out'''
        if tail in t:
            t = t.replace(tail, new_tail, 1)
            open(p, "w", encoding="utf-8", newline=chr(10)).write(t)
            print("th_data patched")
        else:
            print("tail anchor miss")
    else:
        print("already patched")
