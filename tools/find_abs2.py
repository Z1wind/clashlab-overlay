# -*- coding: utf-8 -*-
import os, zipfile
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
z = zipfile.ZipFile(os.path.join(BASE, "out", "release", "ClashLab_open_source_v0.1.0.zip"))
for n in z.namelist():
    b = z.read(n)
    try:
        s = b.decode("utf-8")
    except Exception:
        continue
    if "C:\\Users\\" in s or "C:/Users/" in s:
        print("==", n, len(b))
        for i, line in enumerate(s.splitlines(), 1):
            if "C:\\Users\\" in line or "C:/Users/" in line:
                print("   ", i, line.strip()[:130])
