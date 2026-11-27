# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "war_scout_capture.py")
t = open(p, encoding="utf-8").read()
old = '''        if find(img, "敌军"):
            hit = find(img, "敌军")
            tap(hit[0], hit[1], 3)
            img = screencap(cur)'''
new = '''        _sw = find(img, "敌军") or find(img, "我军")
        if _sw:
            tap(_sw[0], _sw[1], 3)
            img = screencap(cur)'''
if old in t:
    t = t.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("switch handles 我军/敌军")
else:
    print("anchor miss")
