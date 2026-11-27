# -*- coding: utf-8 -*-
import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab import assets
names = [n for n in dir(assets) if n.isupper()]
print("exports:", names[:10])
S = assets.STATS if hasattr(assets, "STATS") else {}
print("STATS entries:", len(S))
sample = list(S.items())[:6]
for k, v in sample:
    print(k, v)
