# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "train_pipeline_full.py")
t = open(p, encoding="utf-8").read()
t = t.replace("import os, random, sys", "import json, os, random, sys", 1)
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("json import added")
