# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "overlay", "pages.py")
t = open(p, encoding="utf-8").read()
if "show_anchor_debug" not in t:
    old = '''    _anchor_brief = "  ".join(
        (f"{a['key']}({a['point'][0]},{a['point'][1]})"
         if a["confirmed"] else f"{a['key']}({a['point'][0]},{a['point'][1]})·未验证")
        for a in anchors[:3]) or "—"
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
    imgui.text_wrapped(_anchor_brief)
    y += 34.0
    if len(anchors) > 3:
        imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
        imgui.text_colored(imgui.ImVec4(*DIM),
                           f"…其余 {len(anchors) - 3} 条见 config/anchors.json")
        y += 16.0'''
    new = '''    # 调试锚点默认隐藏（技术数据，普通用户不需要）；config/overlay.json 里
    # "show_anchor_debug": true 才显示完整锚点坐标。
    _show_dbg = False
    try:
        _ov, _err = data.load_json(os.path.join(root, "config", "overlay.json"))
        _show_dbg = bool((_ov or {}).get("show_anchor_debug", False))
    except Exception:
        _show_dbg = False
    if _show_dbg:
        _anchor_brief = "  ".join(
            (f"{a['key']}({a['point'][0]},{a['point'][1]})"
             if a["confirmed"] else f"{a['key']}({a['point'][0]},{a['point'][1]})·未验证")
            for a in anchors[:3]) or "—"
        imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
        imgui.text_wrapped(_anchor_brief)
        y += 34.0
        if len(anchors) > 3:
            imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
            imgui.text_colored(imgui.ImVec4(*DIM),
                               f"…其余 {len(anchors) - 3} 条见 config/anchors.json")
            y += 16.0'''
    if old in t:
        t = t.replace(old, new, 1)
        open(p, "w", encoding="utf-8", newline="\n").write(t)
        print("debug anchors hidden by default")
    else:
        print("anchor block miss")
