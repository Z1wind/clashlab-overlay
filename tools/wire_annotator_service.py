# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"

# 1) annotator ROOT 支持 frozen（CLASHLAB_ROOT）
p = os.path.join(BASE, "clashlab", "annotator.py")
t = open(p, encoding="utf-8").read()
old = 'ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))'
new = 'ROOT = os.environ.get("CLASHLAB_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))'
if old in t:
    t = t.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("annotator ROOT frozen-aware")

# 2) 面板设置页加「启动标注器」按钮
p2 = os.path.join(BASE, "clashlab", "overlay", "pages.py")
t2 = open(p2, encoding="utf-8").read()
if "start_annotator" not in t2:
    anchor = "    # ---- 面板位置："
    add = '''    # ---- 启动标注器（内置服务，无需命令行）----
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
    if _btn(_L(ready, "启动标注器", "Start annotator"), imgui.ImVec2(160.0, 26.0), key="start_annotator"):
        try:
            from .. import annotator as _ann
            _url, _started = _ann.ensure_running(root)
            ctx.log(("annotator: started " if _started else "annotator: already running ") + _url)
        except Exception as e:
            ctx.log(f"annotator: start failed {e!r}")
    y += 30.0

''' + anchor
    if anchor in t2:
        t2 = t2.replace(anchor, add, 1)
        open(p2, "w", encoding="utf-8", newline="\n").write(t2)
        print("panel start_annotator button added")
    else:
        print("panel anchor miss")
