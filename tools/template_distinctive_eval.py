# -*- coding: utf-8 -*-
"""模板匹配（仅外形独特的建筑类型）留一验证 + 分类型统计。"""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import cv2, numpy as np
from clashlab.geo import Calib
S, T, SEARCH = 96, 64, 8
ONLY = {"town-hall","eagle-artillery","monolith","scattershot","x-bow","inferno-tower",
        "clan-castle","air-sweeper","ricochet-cannon","multi-archer-tower","spell-tower",
        "firespitter","multi-gear-tower"}
def prep(path):
    d = json.load(open(path, encoding="utf-8"))
    img = cv2.imdecode(np.fromfile(os.path.join(BASE, "android", "assets", d["image"]), np.uint8), cv2.IMREAD_GRAYSCALE)
    wn, hn = d["image_size"]; quad = np.float32([[u*wn, v*hn] for u, v in d["corners_norm"]])
    return img, Calib.from_quad(quad, n=44), [(b["type"], b["tile"][0], b["tile"][1]) for b in d["buildings"]]
def warp(img, cal, cx, cy, size):
    x0, y0 = cx-1.5, cy-1.5
    p = [cal.tile_to_px(x0,y0), cal.tile_to_px(x0+4,y0), cal.tile_to_px(x0+4,y0+4), cal.tile_to_px(x0,y0+4)]
    H = cv2.getPerspectiveTransform(np.float32(p), np.float32([[0,0],[size,0],[size,size],[0,size]]))
    return cv2.warpPerspective(img, H, (size,size), flags=cv2.INTER_AREA)
def cc(a, t):
    o = (a.shape[0]-t)//2; return a[o:o+t, o:o+t]
def main():
    paths = [os.path.join(os.path.expanduser("~"), "Downloads", "annot_b%02d.json" % i) for i in range(1, 9)]
    data = []
    for bi, p in enumerate(paths):
        if bi in (0,1): continue
        img, cal, blds = prep(p); data.append({"bi": bi, "img": img, "cal": cal, "blds": blds})
    per_type = {}
    reports = []
    for hold in range(len(data)):
        tr = [b for i,b in enumerate(data) if i != hold]; va = data[hold]
        bank = {}
        for b in tr:
            for (t, gx, gy) in b["blds"]:
                if t not in ONLY: continue
                if len(bank.get(t, [])) >= 6: continue
                bank.setdefault(t, []).append(cc(warp(b["img"], b["cal"], gx, gy, S), T))
        types = sorted(bank)
        img, cal, blds = va["img"], va["cal"], va["blds"]
        gt = [(t, gx+.5, gy+.5) for (t,gx,gy) in blds if t in ONLY]
        gt_all = len(gt)
        cells = [(cx, cy) for cx in range(2,42) for cy in range(2,42)]
        cand = []
        for (cx, cy) in cells:
            full = warp(img, cal, cx, cy, S+2*SEARCH)
            best = (-1.0, -1)
            for cls, t in enumerate(types):
                for tpl in bank[t]:
                    m = float(cv2.matchTemplate(full, tpl, cv2.TM_CCOEFF_NORMED).max())
                    if m > best[0]: best = (m, cls)
            cand.append((best[0], best[1], cx+.5, cy+.5))
        best_f1 = None
        for th in (0.55,0.6,0.65,0.7,0.75,0.8,0.85):
            sel = sorted([c for c in cand if c[0] >= th], reverse=True)
            kept = []
            for c in sel:
                if all(abs(c[2]-q[2]) + abs(c[3]-q[3]) > 1.9 for q in kept): kept.append(c)
            matched = set(); tp = tok = 0; tp_by = {}
            for (s, cls, cx, cy) in kept:
                bb = None
                for gi,(tt,gx,gy) in enumerate(gt):
                    if gi in matched: continue
                    d = abs(cx-gx)+abs(cy-gy)
                    if d < 1.6 and (bb is None or d < bb[0]): bb = (d, gi)
                if bb:
                    matched.add(bb[1]); tp += 1
                    ok = types[cls] == gt[bb[1]][0]
                    if ok: tok += 1
                    key = gt[bb[1]][0]; d = per_type.setdefault(key, {"n":0,"ok":0})
                    d["n"] += 1; d["ok"] += int(ok)
            prec = tp/max(1,len(kept)); rec = tp/max(1,gt_all); f1 = 2*prec*rec/max(1e-9,prec+rec)
            if best_f1 is None or f1 > best_f1[0]: best_f1 = (f1, th, prec, rec, tp, len(kept), tok)
        f1, th, prec, rec, tp, npred, tok = best_f1
        print("hold base %d: distinctive gt=%d pred=%d tp=%d prec=%.3f recall=%.3f f1=%.3f type_acc=%.3f @th=%.2f" % (va["bi"], gt_all, npred, tp, prec, rec, f1, tok/max(1,tp), th), flush=True)
        reports.append({"base": va["bi"], "gt": gt_all, "pred": npred, "tp": tp, "prec": prec, "recall": rec, "f1": f1, "type_acc": tok/max(1,tp), "th": th})
    mean = lambda k: sum(r[k] for r in reports)/len(reports)
    print("DISTINCTIVE TEMPLATE MEAN prec=%.3f recall=%.3f f1=%.3f type_acc=%.3f" % (mean("prec"), mean("recall"), mean("f1"), mean("type_acc")))
    for t, d in sorted(per_type.items(), key=lambda kv: -kv[1]["n"]):
        print("  %-22s n=%d ok=%d acc=%.2f" % (t, d["n"], d["ok"], d["ok"]/max(1,d["n"])))
    json.dump({"reports": reports, "per_type": per_type}, open(os.path.join(BASE,"out","template_distinctive_report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
if __name__ == "__main__":
    main()
