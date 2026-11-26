# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"

p = os.path.join(BASE, "clashlab", "overlay", "pages.py")
t = open(p, encoding="utf-8").read()

# 1) _L 支持显式语言
old = '''def _L(ready, zh, en):
    return en if not ready else zh'''
new = '''def _L(ready, zh, en):
    from . import lang
    mode = lang.get()
    if mode == "en":
        return en
    if mode == "zh":
        return zh
    return en if not ready else zh'''
if old in t:
    t = t.replace(old, new, 1)
    print("_L patched")

# 2) 设置页顶部加语言切换
if "lang.TOGGLE" not in t:
    anchor = '''def _draw_setting(ctx, state, root, ready, panel_w, px, H):
    avail_w = panel_w - 2 * PAD
    paths = data.Paths(root)
    y = _content_top(root)
'''
    add = '''def _draw_setting(ctx, state, root, ready, panel_w, px, H):
    avail_w = panel_w - 2 * PAD
    paths = data.Paths(root)
    y = _content_top(root)

    # ---- 语言切换（简体中文 / English） ----
    lang.ensure_loaded(root)
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
    imgui.text(_L(ready, "语言", "Language"))
    imgui.same_line(0.0, 10.0)
    _cur_lang = lang.get()
    if _btn("中文", (68.0, 24.0), kind="sec", active=_cur_lang in ("zh", "auto")):
        lang.set(root, "zh")
        ctx.log("UI language -> zh")
    imgui.same_line(0.0, 6.0)
    if _btn("English", (84.0, 24.0), kind="sec", active=_cur_lang == "en"):
        lang.set(root, "en")
        ctx.log("UI language -> en")
    imgui.same_line(0.0, 8.0)
    imgui.text_disabled(_L(ready, "（立即生效）", "(applies instantly)"))
    y += 30.0
'''
    if anchor in t:
        t = t.replace(anchor, add, 1)
        open(p, "w", encoding="utf-8", newline="\n").write(t)
        print("settings toggle added")
    else:
        print("settings anchor miss")
else:
    open(p, "w", encoding="utf-8", newline="\n").write(t)
