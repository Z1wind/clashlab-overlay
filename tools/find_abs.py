# -*- coding: utf-8 -*-
import os, zipfile, re
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
zp = os.path.join(BASE, "out", "release", "ClashLab_open_source_v0.1.0.zip")
z = zipfile.ZipFile(zp)
for n in z.namelist():
    if not n.endswith((".py", ".md", ".txt", ".json", ".ps1", ".cmd", ".spec")):
        continue
    s = z.read(n).decode("utf-8", "ignore")
    if "C:\\Users\\" in s or "C:/Users/" in s:
        print("==", n)
        for i, line in enumerate(s.splitlines(), 1):
            if "C:\\Users\\" in line or "C:/Users/" in line:
                print("   ", i, line.strip()[:120])
