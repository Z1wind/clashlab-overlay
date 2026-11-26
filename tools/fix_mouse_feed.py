# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "overlay", "runtime.py")
t = open(p, encoding="utf-8").read()
old = '''        # PANEL 态自喂鼠标（兜底通路，见 _feed_panel_mouse）；HUD 保持穿透不喂
        if rt.state.mode == "PANEL" and not wait:
            _feed_panel_mouse(rt, window, hwnd, io, prev)'''
new = '''        # PANEL 态默认不再自喂鼠标：窗口自身可点击（无 WS_EX_TRANSPARENT），
        # GLFW 原生事件足够；双通道会让同一次点击被注入两次、ImGui 点击被抵消
        # （实测：标签页点击不切换）。需要旧行为时 config/overlay.json 设
        # "panel_mouse_feed": true。
        if rt.state.mode == "PANEL" and not wait:
            if bool(rt.cfg.get("panel_mouse_feed", False)):
                _feed_panel_mouse(rt, window, hwnd, io, prev)'''
if old in t:
    t = t.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("mouse feed disabled by default")
else:
    print("anchor miss")
