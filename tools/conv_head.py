# -*- coding: utf-8 -*-
import os, re
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "out", "tactics", "_convention", "convention_report.md")
s = open(p, encoding="utf-8").read()
print("bytes", len(s))
for line in s.splitlines():
    if any(k in line for k in ("口径", "贴边", "越界", "重叠", "46", "50", "34", "32", "A/B", "总计", "合计")):
        print(line.strip()[:160])
