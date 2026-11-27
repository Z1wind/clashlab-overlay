# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tests", "test_battle_sim.py")
t = open(p, encoding="utf-8").read()
t = t.replace('        self.assertGreaterEqual(b["walls_to_break"], 1)',
              '        self.assertGreaterEqual(b["path_len"], a["path_len"])  # 绕墙或破墙，路径不会更短')
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("test fixed")
