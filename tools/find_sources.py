# -*- coding: utf-8 -*-
import os, re
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
for n in ("01", "02", "03", "04", "05", "06"):
    p = os.path.join(BASE, "bases", "th16", n, "notes.md")
    txt = open(p, encoding="utf-8", errors="replace").read()
    urls = re.findall(r"https?://[^\s)>\"“”]+", txt)
    tags = re.findall(r"#\d{2,5}", txt)
    print(n, "urls:", urls[:4], "tags:", tags[:4])
