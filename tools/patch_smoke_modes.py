# -*- coding: utf-8 -*-
import os, re
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "desktop_app.py")
t = open(p, encoding="utf-8").read()
old = '''                r = api.preannotate([[0.106,0.51],[0.491,-0.104],[0.875,0.508],[0.489,1.133]],
                                    [1600, 735], "img/b03.jpg")
                res = {"ok": r.get("ok"), "n": len(r.get("buildings") or []), "ms": r.get("ms"), "error": r.get("error")}'''
new = '''                corners = [[0.106,0.51],[0.491,-0.104],[0.875,0.508],[0.489,1.133]]
                modes = {}
                for m in ("standard", "recall", "precise"):
                    rr = api.preannotate(corners, [1600, 735], "img/b03.jpg", m)
                    modes[m] = {"ok": rr.get("ok"), "n": len(rr.get("buildings") or []), "ms": rr.get("ms"), "error": rr.get("error")}
                res = {"modes": modes}'''
if old in t:
    t = t.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("smoke2 modes patched")
else:
    print("smoke2 anchor miss")
