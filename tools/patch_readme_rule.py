# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "annotate", "README.md")
t = open(p, encoding="utf-8").read()
anchor = "- 每阵的 quad 就写在 layout.json 的 note 里"
add = ("- 标定规则（重要）：44x44 网格覆盖整张地图的 44 格；四角 = **地图最外圈格的四个角**（通常就是可建造草地边界），"
       "**不是最外侧建筑或墙**。角点贴到墙上会让整张网格缩一圈，所有 tile 都会偏。\n")
if "标定规则（重要）" in t:
    print("already")
elif anchor in t:
    i = t.find(anchor)
    t = t[:i] + add + t[i:]
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("patched README, bytes", len(t.encode()))
else:
    print("anchor missing")
