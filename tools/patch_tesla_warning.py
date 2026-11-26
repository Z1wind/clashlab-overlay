# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "overlay", "giant_arrow_diagram.py")
t = open(p, encoding="utf-8").read()
if "TESLA_WARNING" not in t:
    add = '''

TESLA_WARNING = "⚠ 特斯拉默认不现形：图中格位仅为推测；其 DPS 低，穿云箭收益低"


def tesla_warning(layout):
    """布局里有隐形特斯拉时返回提醒文案，否则返回空串。"""
    for b in (layout or {}).get("buildings") or []:
        if isinstance(b, dict) and b.get("type") in HIDDEN_TYPES:
            return TESLA_WARNING
    return ""
'''
    t = t.rstrip() + "\n" + add
    # 渲染时把提醒画在图例上方
    old = '''    d.text((lx, ly), "图例", font=f_lab, fill=_pr.INK)'''
    new = '''    _warn = tesla_warning(layout)
    if _warn:
        d.text((lx, ly), _warn, font=f_sm, fill=_pr.AMBER)
        ly += lh
    d.text((lx, ly), "图例", font=f_lab, fill=_pr.INK)'''
    if old in t:
        t = t.replace(old, new, 1)
        print("warning injected")
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("tesla warning added")
else:
    print("already")
