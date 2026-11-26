# -*- coding: utf-8 -*-
import re
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
lines = open(BASE + r"\clashlab\th_data.py", encoding="utf-8").read().splitlines()
print("total lines:", len(lines))
for i, l in enumerate(lines, 1):
    if re.match(r"def \w+", l):
        print(i, ":", l)
start = next(i for i, l in enumerate(lines, 1) if l.startswith("def stats("))
for j in range(start - 1, min(start + 70, len(lines))):
    print(j + 1, ":", lines[j])
