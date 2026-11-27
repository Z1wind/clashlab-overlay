# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tests", "test_opponent_th.py")
t = open(p, encoding="utf-8").read()
t = t.replace('s = _opponent_th_suffix({"clan_th_dist": {16: 3, 15: 5, 14: 1}})',
              's = _opponent_th_suffix({"clan_th_dist": {16: 3, 15: 5, 14: 1, 13: 2}})')
t = t.replace('self.assertNotIn("TH14", s)  # 只取前三', 'self.assertNotIn("TH13", s)  # 只取前三')
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("test fixed")
