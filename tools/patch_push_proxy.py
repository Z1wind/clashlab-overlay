# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "push_changes.py")
t = open(p, encoding="utf-8").read()
if "ProxyHandler({})" in t:
    print("push_changes already")
else:
    marker = "import base64, hashlib, json, os, subprocess, sys, time, urllib.error, urllib.request\n"
    if marker in t:
        t = t.replace(marker, marker + "urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))\n", 1)
        open(p, "w", encoding="utf-8", newline="\n").write(t)
        print("push_changes proxy bypass added")
    else:
        print("marker miss")
