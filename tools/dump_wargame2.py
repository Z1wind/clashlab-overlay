# -*- coding: utf-8 -*-
import re
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
lines = open(BASE + r"\clashlab\wargame.py", encoding="utf-8").read().splitlines()
for lo, hi in ((700, 760), (760, 850)):
    print("==== lines %d-%d ====" % (lo, hi))
    for j in range(lo - 1, min(hi, len(lines))):
        print(j + 1, ":", lines[j])
