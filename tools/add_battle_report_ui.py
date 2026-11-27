# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"

# 1) battle_report.build 支持直接传 layout dict
p = os.path.join(BASE, "clashlab", "battle_report.py")
t = open(p, encoding="utf-8").read()
t = t.replace("def build(layout_path, out_path=None, th=None, army=None, open_after=False):",
              "def build(layout_path=None, out_path=None, th=None, army=None, open_after=False, layout=None):")
t = t.replace('''    layout = json.load(open(layout_path, encoding="utf-8"))
    name = layout.get("name") or os.path.splitext(os.path.basename(layout_path))[0]''',
'''    if layout is None:
        layout = json.load(open(layout_path, encoding="utf-8"))
    name = layout.get("name") or (os.path.splitext(os.path.basename(layout_path))[0] if layout_path else "current")''')
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("battle_report dict support")

# 2) 面板设置页加「生成战报」按钮（在启动标注器按钮后）
p2 = os.path.join(BASE, "clashlab", "overlay", "pages.py")
t2 = open(p2, encoding="utf-8").read()
if "make_battle_report" not in t2:
    anchor = "    # ---- 启动标注器（内置服务，无需命令行）----"
    add = '''    # ---- 生成战报（当前阵型 → HTML）----
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
    if _btn(_L(ready, "生成战报", "Battle report"), imgui.ImVec2(160.0, 26.0), key="make_battle_report"):
        try:
            from .. import battle_report as _br
            lay = getattr(state, "layout", None) or getattr(state, "Layout", None)
            if isinstance(lay, dict) and lay.get("buildings"):
                r = _br.build(None, layout=lay, th=16, open_after=True)
                ctx.log(f"battle report: {r.get('grade')} {r.get('score')} -> {r.get('path')}")
            else:
                ctx.log("battle report: 当前没有阵型数据（先加载/标注阵型）")
        except Exception as e:
            ctx.log(f"battle report failed: {e!r}")
    y += 30.0

''' + anchor
    if anchor in t2:
        t2 = t2.replace(anchor, add, 1)
        open(p2, "w", encoding="utf-8", newline="\n").write(t2)
        print("panel battle report button added")
    else:
        print("panel anchor miss")
