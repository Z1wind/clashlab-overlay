# -*- coding: utf-8 -*-
import hashlib, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "dist", "ClashLabAnnotator_Desktop_v2.0.exe")
data = open(p, "rb").read()
print("LOCAL_SHA256", hashlib.sha256(data).hexdigest())
print("LOCAL_MD5", hashlib.md5(data).hexdigest().upper(), "SIZE", len(data))
