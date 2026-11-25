# -*- coding: utf-8 -*-
import os, sys, json
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, os.path.join(BASE, "out", "tactics", "_convention"))
import check_convention as cc
bases = cc.load_bases()
rows = cc.recount_oob(bases)
print("n", len(rows), "type", type(rows[0]).__name__)
print("first:", json.dumps(rows[0], ensure_ascii=False))
print("second:", json.dumps(rows[1], ensure_ascii=False))
