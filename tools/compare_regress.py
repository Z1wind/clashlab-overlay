# -*- coding: utf-8 -*-
import glob, json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ok = True
for d in sorted(glob.glob(os.path.join(BASE, "out", "enemy_report", "0*_annotated"))):
    n = os.path.basename(d)
    a = json.load(open(os.path.join(d, "report.json"), encoding="utf-8"))
    b = json.load(open(os.path.join(BASE, "out", "enemy_report", "_regress", n, "report.json"), encoding="utf-8"))
    sa, sb = a.get("score") or {}, b.get("score") or {}
    ba, bb = a.get("arrow_best") or {}, b.get("arrow_best") or {}
    same = (a.get("buildings") == b.get("buildings")
            and sa.get("overall") == sb.get("overall") and sa.get("grade") == sb.get("grade")
            and ba.get("from") == bb.get("from") and ba.get("to") == bb.get("to")
            and len(ba.get("hits") or []) == len(bb.get("hits") or [])
            and len(a.get("arrow_candidates") or []) == len(b.get("arrow_candidates") or []))
    ok = ok and same
    print(n, "fields_match=%s score=%s grade=%s hits=%s/%s" % (
        same, sb.get("overall"), sb.get("grade"), len(ba.get("hits") or []), len(bb.get("hits") or [])))
print("ALL_MATCH", ok)
