# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "overlay", "pages.py")
t = open(p, encoding="utf-8").read()
if "open_units" not in t:
    anchor = "    # ---- 面板位置：右 / 下 / 内（外置窗口；落盘 config/overlay.json，默认右） ----"
    add = '''    # ---- 兵种/法术表（内置页面） ----
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
    if _btn(_L(ready, "打开兵种/法术表", "Open troop/spell table"), imgui.ImVec2(160.0, 26.0), key="open_units"):
        try:
            import os as _os
            _cand = [_os.path.join(root, "dist", "units.html"), _os.path.join(root, "out", "units.html")]
            _hit = next((c for c in _cand if _os.path.exists(c)), None)
            if _hit and hasattr(_os, "startfile"):
                _os.startfile(_hit)
                ctx.log("units: opened " + _hit)
            else:
                ctx.log("units: page not found (run tools/build_units_page.py)")
        except Exception as e:
            ctx.log(f"units: open failed {e!r}")
    y += 30.0

''' + anchor
    if anchor in t:
        t = t.replace(anchor, add, 1)
        open(p, "w", encoding="utf-8", newline="\n").write(t)
        print("panel open_units button added")
    else:
        print("anchor miss again")
else:
    print("already")
