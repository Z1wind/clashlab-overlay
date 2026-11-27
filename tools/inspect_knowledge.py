# -*- coding: utf-8 -*-
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
idx = json.load(open(os.path.join(BASE, "knowledge", "index.json"), encoding="utf-8"))
print("index type:", type(idx).__name__, "len:", len(idx))
print("index[0]:", json.dumps(idx[0], ensure_ascii=False)[:400] if idx else None)
tr = json.load(open(os.path.join(BASE, "knowledge", "th_ruleset.json"), encoding="utf-8"))
print("th_ruleset type:", type(tr).__name__)
if isinstance(tr, dict):
    print("keys:", list(tr.keys())[:8])
    k = list(tr.keys())[0]
    print("sample:", json.dumps(tr[k], ensure_ascii=False)[:500])
