# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "docs", "NEXT_STEPS.md")
t = open(p, encoding="utf-8").read()
if "本机位置（2026-11-26 迁移）" not in t:
    t = t.rstrip() + chr(10) + '''## 本机位置（2026-11-26 迁移）

项目已迁到 E:\\ClashLab；旧路径 C:\\Users\\Admin（无密码）\\Doubao\\chats\\2026-11-23\\new-chat 是 Junction（C 盘 0 字节），命令照旧可用。
'''
    open(p, "w", encoding="utf-8", newline=chr(10)).write(t)
    print("next steps updated")
