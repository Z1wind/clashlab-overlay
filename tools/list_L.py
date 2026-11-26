# -*- coding: utf-8 -*-
import re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
t = open(r"clashlab\overlay\pages.py", encoding="utf-8").read()
pairs = re.findall(r'_L\(ready,\s*"([^"]*)",\s*"([^"]*)"\)', t)
seen = []
for zh, en in pairs:
    if (zh, en) not in seen:
        seen.append((zh, en))
print("pairs:", len(seen))
for zh, en in seen[:80]:
    print("%-24s | %s" % (zh, en))
