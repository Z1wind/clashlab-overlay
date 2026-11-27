# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
old_fwd = '''        x = self.p1(self.d1(x)); x = self.p2(self.d2(x))
        x = self.d3(x); x = self.up(x); x = self.d4(x); x = self.up(x)
        return self.head(x)'''
new_fwd = '''        x = self.p1(self.d1(x)); x = self.p2(self.d2(x))
        x = self.d3(x)  # stride 4 -> 160x160
        return self.head(x)'''
for name in ("centernet_mini.py", "eval_centernet_real.py"):
    p = os.path.join(BASE, "tools", name)
    t = open(p, encoding="utf-8").read()
    if old_fwd in t:
        t = t.replace(old_fwd, new_fwd, 1)
        open(p, "w", encoding="utf-8", newline="\n").write(t)
        print("patched", name)
    else:
        print("miss", name)
