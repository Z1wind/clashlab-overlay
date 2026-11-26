# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
gi = os.path.join(BASE, ".gitignore")
t = open(gi, encoding="utf-8").read()
add = "\n# Android 构建产物与图片副本\nandroid/build/\nandroid/dist/\nandroid/assets/img/\nandroid/debug.keystore\n"
if "android/assets/img" not in t:
    open(gi, "w", encoding="utf-8", newline="\n").write(t.rstrip() + add)
    print("gitignore updated")
