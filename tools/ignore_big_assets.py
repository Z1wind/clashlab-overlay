# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
gi = os.path.join(BASE, ".gitignore")
t = open(gi, encoding="utf-8").read()
add = "\n# 第三方素材/数据集（本地训练用，不入库）\nassets/clashking/\ndatasets/\n"
if "assets/clashking" not in t:
    open(gi, "w", encoding="utf-8", newline="\n").write(t.rstrip() + add)
    print("gitignore updated")
