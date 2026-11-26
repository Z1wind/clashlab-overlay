# -*- coding: utf-8 -*-
import json, os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
summ = os.path.join(BASE, "out", "annotate", "summary.json")
if os.path.exists(summ):
    s = json.load(open(summ, encoding="utf-8"))
    print("summary:", json.dumps(s, ensure_ascii=False)[:700])
for n in ("01", "02", "03", "04", "05", "06"):
    p = os.path.join(BASE, "out", "annotate", n + "_annotated.json")
    if not os.path.exists(p):
        print(n, "MISSING"); continue
    d = json.load(open(p, encoding="utf-8"))
    note = (d.get("note") or "")
    print(n, "buildings=", len(d.get("buildings") or []), "walls=", len(d.get("walls") or []),
          "grid=", d.get("grid"), "has_quad=", ("quad" in note),
          "| note_tail=", note[-60:].replace(chr(10), " "))
for n in ("01", "02", "03", "04", "05", "06"):
    q = os.path.join(BASE, "out", "annotate", n + "_quad.json")
    if os.path.exists(q):
        print("override", n, json.load(open(q, encoding="utf-8")).get("quad"))
