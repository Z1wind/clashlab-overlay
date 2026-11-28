# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
# smoke2 增加 supplement 验证
p = os.path.join(BASE, "tools", "desktop_app.py")
t = open(p, encoding="utf-8").read()
old = '''                for m in ("standard", "recall", "precise"):
                    rr = api.preannotate(corners, [1600, 735], "img/b03.jpg", m)
                    modes[m] = {"ok": rr.get("ok"), "n": len(rr.get("buildings") or []), "ms": rr.get("ms"), "error": rr.get("error")}
                res = {"modes": modes}'''
new = '''                for m in ("standard", "recall", "precise"):
                    rr = api.preannotate(corners, [1600, 735], "img/b03.jpg", m)
                    modes[m] = {"ok": rr.get("ok"), "n": len(rr.get("buildings") or []), "ms": rr.get("ms"), "error": rr.get("error")}
                base = api.preannotate(corners, [1600, 735], "img/b03.jpg", "standard")
                keep = [[b["tile"][0] + 1, b["tile"][1] + 1] for b in (base.get("buildings") or [])[:10]]
                r2 = api.preannotate(corners, [1600, 735], "img/b03.jpg", "standard", keep)
                res = {"modes": modes, "supplement": {"ok": r2.get("ok"), "n": len(r2.get("buildings") or []), "existing": len(keep), "ms": r2.get("ms")}}'''
if old in t:
    t = t.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("smoke supplement patched")
else:
    print("smoke anchor miss")
