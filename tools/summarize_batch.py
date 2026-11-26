# -*- coding: utf-8 -*-
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
d = json.load(open(os.path.join(ROOT, "out", "arrow_batch", "report.json"), encoding="utf-8"))
rows = d["cases"]
real = [r for r in rows if not r["name"].startswith("synth")]
syn = [r for r in rows if r["name"].startswith("synth")]
def stat(rs):
    n = len(rs)
    st = sum(1 for r in rs if r["stable"])
    fl = sum(1 for r in rs if r["flips"])
    sw = sum(1 for r in rs if r["best_sweeper"])
    return n, st, fl, sw
for label, rs in (("all", rows), ("real", real), ("synth", syn)):
    n, st, fl, sw = stat(rs)
    print("%-6s n=%3d stable=%3d (%.0f%%) flip_cases=%d sweeper_best=%d" % (label, n, st, 100.0*st/n, fl, sw))
print("--- 5 worst (most distinct signatures) ---")
for r in sorted(rows, key=lambda x: -x["distinct"])[:5]:
    print("%-26s blds=%2d distinct=%2d flip=%2d stable=%s target=%s" % (r["name"], r["buildings"], r["distinct"], r["flips"], r["stable"], r["queen_target"]))
print("--- 5 best stable cases ---")
for r in [x for x in rows if x["stable"]][:5]:
    print("%-26s blds=%2d score=%s hits=%s sweeper=%s target=%s" % (r["name"], r["buildings"], r["best_score"], r["best_hits"], r["best_sweeper"], r["queen_target"]))
