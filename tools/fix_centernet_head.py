# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
bad = '''        x = self.p1(self.d1(x)); x = self.p2(self.d2(x))
        x = self.d3(x)  # stride 4 -> 160x160
        return self.head(x)'''
good = '''        x = self.p1(self.d1(x)); x = self.p2(self.d2(x))
        x = self.d3(x)   # 96ch @160
        x = self.d4(x)   # 128ch @160
        return self.head(x)'''
for name in ("centernet_mini.py", "eval_centernet_real.py"):
    p = os.path.join(BASE, "tools", name)
    t = open(p, encoding="utf-8").read()
    if bad in t:
        t = t.replace(bad, good, 1); open(p, "w", encoding="utf-8", newline="\n").write(t); print("patched", name)
    else:
        print("miss", name)
