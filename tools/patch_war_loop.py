# -*- coding: utf-8 -*-

import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"

# 1) 修侦察流水线：循环内若出现「敌军」按钮则先切到敌军侧
p = os.path.join(BASE, "tools", "war_scout_capture.py")
t = open(p, encoding="utf-8").read()
t = t.replace('''    shots = 0
    for i in range(a.start, a.start + a.max):
        img = screencap(cur)''',
'''    shots = 0
    for i in range(a.start, a.start + a.max):
        img = screencap(cur)
        if find(img, "敌军"):
            hit = find(img, "敌军")
            tap(hit[0], hit[1], 3)
            img = screencap(cur)''')
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("pipeline enemy-side loop patched")
