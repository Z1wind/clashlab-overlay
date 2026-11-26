# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "overlay", "pages.py")
t = open(p, encoding="utf-8").read()
if '_btn(f"清除##{aid}"' in t:
    t = t.replace('_btn(f"清除##{aid}"', '_btn(f"{_L(ready, \'清除\', \'Clear\')}##{aid}"', 1)
    print("clear label translated")
# 设置页内容整体下移，避开引擎按钮的说明行
old = '''def _draw_setting(ctx, state, root, ready, panel_w, px, H):
    avail_w = panel_w - 2 * PAD
    paths = data.Paths(root)
    y = _content_top(root)'''
new = '''def _draw_setting(ctx, state, root, ready, panel_w, px, H):
    avail_w = panel_w - 2 * PAD
    paths = data.Paths(root)
    # 顶部固定栈（标签/状态/引擎按钮+说明）约占到 content_top+34，
    # 设置页从这里再往下排，避免锚点行压住引擎说明（实机重叠问题）。
    y = _content_top(root) + 34.0'''
if old in t:
    t = t.replace(old, new, 1)
    print("settings shifted down")
open(p, "w", encoding="utf-8", newline="\n").write(t)
