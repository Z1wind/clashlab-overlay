# -*- coding: utf-8 -*-
import glob, json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
for d in sorted(glob.glob(os.path.join(BASE, "out", "enemy_report", "0*"))):
    rp = os.path.join(d, "report.json")
    r = json.load(open(rp, encoding="utf-8"))
    sc = r.get("score") or {}
    print("==", os.path.basename(d), "buildings", r.get("buildings"))
    print("  score:", {k: sc.get(k) for k in list(sc)[:6]})
    b = r.get("arrow_best") or {}
    print("  arrow:", {k: b.get(k) for k in ("from", "to", "score", "hits", "tesla_warning")})
    cands = r.get("arrow_candidates") or []
    print("  candidates:", len(cands))
    for c in cands[:2]:
        print("    ", {k: c.get(k) for k in ("from", "to", "score", "hits")})
    ps = r.get("placement_sensitivity") or r.get("sensitivity")
    print("  sensitivity:", str(ps)[:200])
    print("  files:", os.listdir(d))
