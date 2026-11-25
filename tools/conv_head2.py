# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "out", "tactics", "_convention", "convention_report.md")
s = open(p, encoding="utf-8").read()
out = []
for line in s.splitlines():
    t = line.strip()
    if any(k in t for k in ("口径", "贴边", "越界", "重叠", "总计", "合计", "A=", "B=", "C=", "46", "50", "34", "32")):
        out.append(t[:170])
open(os.path.join(BASE, "out", "tactics", "_convention", "_head_ascii.txt"), "w", encoding="utf-8").write("\n".join(out))
print("lines", len(out))
