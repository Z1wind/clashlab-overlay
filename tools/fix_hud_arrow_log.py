# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"

# 1) HUD 穿云箭：加日志（只记一次），便于定位
p = os.path.join(BASE, "clashlab", "overlay", "runtime.py")
t = open(p, encoding="utf-8").read()
if "hud-arrow" not in t:
    old = '''                try:
                    from . import giant_arrow_hud
                    _gap = giant_arrow_hud.load_overlay_plan(rt.root)
                    if _gap:
                        giant_arrow_hud.draw_giant_arrow(dl, rt.calib, _gap, 1280.0, 720.0)
                except Exception:
                    pass'''
    new = '''                try:
                    from . import giant_arrow_hud
                    _gap = giant_arrow_hud.load_overlay_plan(rt.root)
                    if _gap:
                        _n = giant_arrow_hud.draw_giant_arrow(dl, rt.calib, _gap, 1280.0, 720.0)
                        if not prev.get("hud_arrow_logged"):
                            prev["hud_arrow_logged"] = True
                            rt.log(f"hud-arrow: plan from={_gap.get('from')} to={_gap.get('to')} hits_drawn={_n}")
                    elif not prev.get("hud_arrow_missing"):
                        prev["hud_arrow_missing"] = True
                        rt.log("hud-arrow: no config/giant_arrow_overlay.json")
                except Exception as e:
                    if not prev.get("hud_arrow_err"):
                        prev["hud_arrow_err"] = True
                        rt.log(f"hud-arrow error: {e!r}")'''
    if old in t:
        t = t.replace(old, new, 1)
        print("hud arrow logging added")
    else:
        print("hud arrow anchor miss")
open(p, "w", encoding="utf-8", newline="\n").write(t)

# 2) 研究页再下移 16px（按钮压引擎说明）
p2 = os.path.join(BASE, "clashlab", "overlay", "pages.py")
t2 = open(p2, encoding="utf-8").read()
t2 = t2.replace('    y = _content_top(root) + 18.0', '    y = _content_top(root) + 34.0', 1)
open(p2, "w", encoding="utf-8", newline="\n").write(t2)
print("research y -> +34")
