# -*- coding: utf-8 -*-
import json, re
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
for rel in (r"bases\th16\02\layout.json", r"out\annotate\02_annotated.json"):
    d = json.load(open(BASE + "\\" + rel, encoding="utf-8"))
    note = d.get("note") or ""
    i = note.find("quad")
    print("==", rel, "| note len", len(note), "| idx", i)
    print(note[max(0,i-40):i+260].replace(chr(10), " "))
