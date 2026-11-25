# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "out", "overlay", "overlay.log")
s = open(p, "rb").read().decode("utf-8", "replace")
lines = s.splitlines()
tail = [l for l in lines if l.startswith("[13:4") or l.startswith("[13:5")]
print("total_lines", len(lines), "recent", len(tail))
for l in tail[-25:]:
    print("".join(ch if 32 <= ord(ch) < 127 or ord(ch) > 0x2E80 else " " for ch in l)[:160])
