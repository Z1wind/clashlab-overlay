# -*- coding: utf-8 -*-
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
lines = open(BASE + r"\clashlab\wargame.py", encoding="utf-8").read().splitlines()
for j in range(820, min(900, len(lines))):
    print(j + 1, ":", lines[j])
