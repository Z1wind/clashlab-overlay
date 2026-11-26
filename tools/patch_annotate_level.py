# -*- coding: utf-8 -*-
"""C1：annotate_core 保留建筑 level 字段。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "annotate", "annotate_core.py")
t = open(p, encoding="utf-8").read()
old = '''            buildings.append({
                "type": str(b.get("type") or ""),
                "tile": [tx, ty],
                "source": str(b.get("source") or "manual"),
                "conf": conf,
                "note": str(b.get("note") or ""),
            })'''
new = '''            item = {
                "type": str(b.get("type") or ""),
                "tile": [tx, ty],
                "source": str(b.get("source") or "manual"),
                "conf": conf,
                "note": str(b.get("note") or ""),
            }
            # 等级（可选）：标注工具里填的整数，1..99；其它值丢弃
            lv = b.get("level")
            if isinstance(lv, int) and not isinstance(lv, bool) and 1 <= lv <= 99:
                item["level"] = int(lv)
            buildings.append(item)'''
if old in t:
    t = t.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline=chr(10)).write(t)
    print("annotate_core patched")
else:
    print("anchor miss")
