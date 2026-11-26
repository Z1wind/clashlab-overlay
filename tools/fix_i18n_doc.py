# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
p = os.path.join(BASE, "docs", "I18N.md")
t = open(p, encoding="utf-8").read()
old = "- " + BT + "en" + BT + "：强制英文"
if "zh-hant" not in t:
    t = t.replace(old,
        "- " + BT + "zh-hant" + BT + "：繁體中文（设置页按「繁體」；由 zhconv 做簡→繁轉換）；\n" + old)
    t = t.replace("（auto / zh / en）", "（auto / zh / zh-hant / en）")
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("I18N doc fixed")
else:
    print("already has zh-hant")
