# -*- coding: utf-8 -*-
import re
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = BASE + r"\tools\annotate\index.html"
t = open(p, encoding="utf-8").read()
print("calibBar occurrences:", t.count('id="calibBar"'))
print("absolute CSS remains:", "position:absolute;left:12px;right:12px;top:12px;z-index:15" in t)
print("static CSS present:", "校准提示条改成" in t)
if "var best = -1, bestD = 18;" in t:
    t = t.replace("var best = -1, bestD = 18;", "var best = -1, bestD = 26;")
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("hit radius enlarged to 26")
else:
    print("hit radius already changed or anchor missing")
