# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "overlay", "pages.py")
t = open(p, encoding="utf-8").read()
old = '''    doc = _doc_cached(root)
    rows = doc.get("rows") or []
    y = _content_top(root)'''
new = '''    doc = _doc_cached(root)
    rows = doc.get("rows") or []
    # 顶部固定栈（标签/状态/引擎按钮+两行说明）约占 content_top+50；
    # 本地面板从说明行下方开始，避免「刷新情报/统计」压住引擎说明（实机重叠）。
    y = _content_top(root) + 56.0'''
if old in t:
    t = t.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("local y -> +56")
else:
    print("anchor miss")
