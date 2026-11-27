# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tests", "test_battle_sim.py")
t = open(p, encoding="utf-8").read()
old = '''        walled = {"buildings": [{"type": "town-hall", "tile": [20, 20]}],
                  "walls": [[x, 12] for x in range(4, 40)]}'''
new = '''        ring = []
        for x in range(10, 31):
            ring += [[x, 10], [x, 30]]
        for y in range(10, 31):
            ring += [[10, y], [30, y]]
        walled = {"buildings": [{"type": "town-hall", "tile": [20, 20]}], "walls": ring}'''
if old in t:
    t = t.replace(old, new, 1)
    t = t.replace('self.assertGreaterEqual(b["path_len"], a["path_len"])  # 绕墙或破墙，路径不会更短',
                  'self.assertGreaterEqual(b["walls_to_break"], 1)  # 闭合墙必须破墙进入')
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("test ring patched")
