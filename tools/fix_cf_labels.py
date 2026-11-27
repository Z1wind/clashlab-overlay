# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "centernet_fast.py")
t = open(p, encoding="utf-8").read()
old = '''def target_of(path):
    hm = np.zeros((NC, HS, HS), np.float32); sz = np.zeros((2, HS, HS), np.float32)
    lp = path[:-4] + ".txt"'''
new = '''def target_of(path):
    hm = np.zeros((NC, HS, HS), np.float32); sz = np.zeros((2, HS, HS), np.float32)
    # labels 在 labels/<split>/ 下，不在 images 下
    lp = path.replace(os.sep + "images" + os.sep, os.sep + "labels" + os.sep)[:-4] + ".txt"'''
if old in t:
    t = t.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("label path fixed")
else:
    print("anchor miss")
