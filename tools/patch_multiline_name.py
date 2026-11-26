# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "ocr_screen.py")
t = open(p, encoding="utf-8").read()
old = '''    name = named[0] if named else None
    clan = named[1] if len(named) > 1 else None
    return {"level": level, "name": name, "clan": clan, "tag": tag}'''
new = '''    # 玩家名可能折成两行（如 SUVRO / Sumon 2）：>=3 行时最后一行是部落，
    # 中间全部并入名字；两张时保持 name/clan。
    if len(named) >= 3:
        name = " ".join(named[:-1])
        clan = named[-1]
    else:
        name = named[0] if named else None
        clan = named[1] if len(named) > 1 else None
    return {"level": level, "name": name, "clan": clan, "tag": tag}'''
if old in t:
    t = t.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("multiline name parser fixed")

pp = os.path.join(BASE, "tests", "test_ocr_screen.py")
s = open(pp, encoding="utf-8").read()
if "test_multiline_name" not in s:
    s = s.replace("if __name__ == \"__main__\":", '''    def test_multiline_name(self):
        from clashlab.ocr_screen import _parse_lines
        got = _parse_lines(["9. SUVRO", "Sumon 2", "20", "babY WaRioR"])
        self.assertEqual(got["name"], "SUVRO Sumon 2")
        self.assertEqual(got["clan"], "babY WaRioR")

if __name__ == "__main__":''')
    open(pp, "w", encoding="utf-8", newline="\n").write(s)
    print("test added")
