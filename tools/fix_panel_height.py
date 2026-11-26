# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "overlay", "runtime.py")
t = open(p, encoding="utf-8").read()
old = '''    if zone == "right":
        h = float(min(th, sh))
        y = float(max(0, min(ty, sh - int(h))))
        x = float(tx + tw + PANEL_GAP)
        if h < PANEL_MIN_H or x < 0 or x + PANEL_PW > sw:
            return None
        return (x, y, PANEL_PW, h)'''
new = '''    if zone == "right":
        # 面板内容需要约 700px 高；目标客户区常常只有 ~560（1280x720 缩放），
        # 之前直接取 th 导致设置页底部被裁。这里取 max(th, 700) 并夹进工作区。
        h = float(min(max(float(th), 700.0), float(work_bottom - ty), float(sh)))
        y = float(max(0, min(ty, sh - int(h))))
        x = float(tx + tw + PANEL_GAP)
        if h < PANEL_MIN_H or x < 0 or x + PANEL_PW > sw:
            return None
        return (x, y, PANEL_PW, h)'''
if old in t:
    t = t.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("panel height fixed")
else:
    print("anchor miss")
