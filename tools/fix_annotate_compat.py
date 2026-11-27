# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "annotate_web.py")
t = open(p, encoding="utf-8").read()
if "serve = annotator.serve" not in t:
    t = t.replace("from clashlab import annotator\n",
                  "from clashlab import annotator\n\nserve = annotator.serve  # 向后兼容旧测试/脚本\nSTATE = annotator.STATE\n")
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("compat serve re-exported")
