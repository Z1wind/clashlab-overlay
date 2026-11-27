# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "war_base_montage.py")
t = open(p, encoding="utf-8").read()
if "def _nms(" not in t:
    t = t.replace("def montage(img, quad, items, out_prefix, tag=\"\"):",
'''def _nms(items, min_dist=1.6):
    """按置信度删除相邻重复候选（同一建筑只留一个）。"""
    out = []
    for it in items:
        x, y = it["tile"]
        if all(abs(x - o["tile"][0]) >= min_dist or abs(y - o["tile"][1]) >= min_dist for o in out):
            out.append(it)
    return out


def montage(img, quad, items, out_prefix, tag=""):''')
    t = t.replace('''    made = []
    for b in range((len(items) + PER - 1) // PER):''',
'''    items = _nms(items)
    made = []
    for b in range((len(items) + PER - 1) // PER):''')
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("NMS added")
