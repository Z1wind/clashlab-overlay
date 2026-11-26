# -*- coding: utf-8 -*-
import io, re
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
lines = open(BASE + r"\clashlab\wargame.py", encoding="utf-8").read().splitlines()
for i, l in enumerate(lines, 1):
    if re.match(r"def (parse_layout|_run_trials|_run_worker|run|_expand_units|simulate_once)\b", l):
        print(i, ":", l)
# print parse_layout body
start = next(i for i, l in enumerate(lines, 1) if l.startswith("def parse_layout"))
for j in range(start - 1, min(start + 60, len(lines))):
    print(j + 1, ":", lines[j])
