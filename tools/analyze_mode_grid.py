# -*- coding: utf-8 -*-
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
rows = json.load(open(os.path.join(BASE, "out", "mode_threshold_grid.json"), encoding="utf-8"))
def f1(r): return 2*r["prec"]*r["recall"]/max(1e-9, r["prec"]+r["recall"])
print("current app settings:")
for name,(g,e) in {"standard":(0.85,0.85), "recall":(0.70,0.70), "precise":(0.92,0.92)}.items():
    r = next((x for x in rows if abs(x["g"]-g)<1e-6 and abs(x["e"]-e)<1e-6), None)
    if r: print("  %-8s g=%.2f e=%.2f P=%.3f R=%.3f F1=%.3f type=%.3f pred=%.0f" % (name, g, e, r["prec"], r["recall"], f1(r), r["type"], r["pred"]))
print("\nbest by objective:")
std = max(rows, key=f1)
print("  std   (max F1)        g=%.2f e=%.2f P=%.3f R=%.3f F1=%.3f type=%.3f" % (std["g"], std["e"], std["prec"], std["recall"], f1(std), std["type"]))
for prec_min in (0.55, 0.60, 0.65, 0.70):
    cand = [r for r in rows if r["prec"] >= prec_min]
    if cand:
        b = max(cand, key=lambda r: r["recall"])
        print("  recall P>=%.2f        g=%.2f e=%.2f P=%.3f R=%.3f F1=%.3f type=%.3f" % (prec_min, b["g"], b["e"], b["prec"], b["recall"], f1(b), b["type"]))
for rec_min in (0.60, 0.65, 0.70, 0.75):
    cand = [r for r in rows if r["recall"] >= rec_min]
    if cand:
        b = max(cand, key=lambda r: r["prec"])
        print("  precise R>=%.2f      g=%.2f e=%.2f P=%.3f R=%.3f F1=%.3f type=%.3f" % (rec_min, b["g"], b["e"], b["prec"], b["recall"], f1(b), b["type"]))
