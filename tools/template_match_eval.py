# -*- coding: utf-8 -*-
"""关键贴图特征比对：用已标建筑裁片当模板，做 NCC 多尺度/位移匹配，留一验证。

对比 CNN 方案（prec 71.5% / recall 45.6% / type 87.4%）
"""
import json, os, random, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import cv2, numpy as np
from clashlab.geo import Calib
from clashlab.assets import STATS
S = 96          # 候选窗口
T = 64          # 模板尺寸
SEARCH = 8      # ±像素搜索
def prep(path):
    d = json.load(open(path, encoding="utf-8"))
    img = cv2.imdecode(np.fromfile(os.path.join(BASE, "android", "assets", d["image"]), np.uint8), cv2.IMREAD_GRAYSCALE)
    wn, hn = d["image_size"]; quad = np.float32([[u*wn, v*hn] for u, v in d["corners_norm"]])
    cal = Calib.from_quad(quad, n=44)
    blds = [(b["type"], b["tile"][0], b["tile"][1]) for b in d["buildings"]]
    return img, cal, blds
def warp(img, cal, cx, cy, size, margin=0.0):
    # 以 (cx+.5, cy+.5) 为建筑中心，取 4x4 格窗口
    x0, y0 = cx - 1.5 - margin, cy - 1.5 - margin
    x1, y1 = x0 + 4 + 2*margin, y0 + 4 + 2*margin
    p = [cal.tile_to_px(x0,y0), cal.tile_to_px(x1,y0), cal.tile_to_px(x1,y1), cal.tile_to_px(x0,y1)]
    H = cv2.getPerspectiveTransform(np.float32(p), np.float32([[0,0],[size,0],[size,size],[0,size]]))
    return cv2.warpPerspective(img, H, (size,size), flags=cv2.INTER_AREA)
def center_crop(a, t):
    o = (a.shape[0] - t)//2
    return a[o:o+t, o:o+t]
def main():
    paths = [os.path.join(os.path.expanduser("~"), "Downloads", "annot_b%02d.json" % i) for i in range(1, 9)]
    data = []
    for bi, p in enumerate(paths):
        if bi in (0, 1): continue
        img, cal, blds = prep(p); data.append({"bi": bi, "img": img, "cal": cal, "blds": blds})
    print("bases", len(data), flush=True)
    reports = []
    for hold in range(len(data)):
        tr = [b for i, b in enumerate(data) if i != hold]; va = data[hold]
        # 模板库：每类最多 6 个（取不同基）
        bank = {}
        for b in tr:
            for (t, gx, gy) in b["blds"]:
                if len(bank.get(t, [])) >= 6: continue
                w = warp(b["img"], b["cal"], gx, gy, S)
                bank.setdefault(t, []).append(center_crop(w, T))
        types = sorted(bank.keys())
        print("hold", va["bi"], "templates", sum(len(v) for v in bank.values()), "types", len(types), flush=True)
        # 评估
        img, cal, blds = va["img"], va["cal"], va["blds"]
        gt = [(t, gx + .5, gy + .5) for (t, gx, gy) in blds]
        cells = [(cx, cy) for cx in range(2, 42) for cy in range(2, 42)]
        best_by_cell = []
        for (cx, cy) in cells:
            full = warp(img, cal, cx, cy, S + 2*SEARCH)
            best = (-1.0, -1)
            for cls, tpls in enumerate([bank[t] for t in types]):
                for tpl in tpls:
                    res = cv2.matchTemplate(full, tpl, cv2.TM_CCOEFF_NORMED)
                    m = float(res.max())
                    if m > best[0]: best = (m, cls)
            best_by_cell.append((best[0], best[1], cx + .5, cy + .5))
        best_f1 = None
        for th in (0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85):
            sel = sorted([c for c in best_by_cell if c[0] >= th], reverse=True)
            kept = []
            for c in sel:
                if all(abs(c[2]-q[2]) + abs(c[3]-q[3]) > 1.9 for q in kept): kept.append(c)
            matched = set(); tp = tok = 0
            for (s, cls, cx, cy) in kept:
                bb = None
                for gi, (tt, gx, gy) in enumerate(gt):
                    if gi in matched: continue
                    d = abs(cx-gx) + abs(cy-gy)
                    if d < 1.6 and (bb is None or d < bb[0]): bb = (d, gi)
                if bb:
                    matched.add(bb[1]); tp += 1
                    if types[cls] == gt[bb[1]][0]: tok += 1
            prec = tp/max(1,len(kept)); rec = tp/max(1,len(gt)); f1 = 2*prec*rec/max(1e-9, prec+rec)
            if best_f1 is None or f1 > best_f1[0]: best_f1 = (f1, th, prec, rec, tp, len(kept), tok)
        f1, th, prec, rec, tp, npred, tok = best_f1
        tacc = tok/max(1,tp)
        print("hold base %d: gt=%d pred=%d tp=%d prec=%.3f recall=%.3f f1=%.3f type_acc=%.3f @th=%.2f" % (va["bi"], len(gt), npred, tp, prec, rec, f1, tacc, th), flush=True)
        reports.append({"base": va["bi"], "gt": len(gt), "pred": npred, "tp": tp, "prec": prec, "recall": rec, "f1": f1, "type_acc": tacc, "th": th})
    mean = lambda k: sum(r[k] for r in reports)/len(reports)
    print("TEMPLATE MATCH MEAN prec=%.3f recall=%.3f f1=%.3f type_acc=%.3f" % (mean("prec"), mean("recall"), mean("f1"), mean("type_acc")))
    json.dump({"reports": reports, "mean": {"prec": mean("prec"), "recall": mean("recall"), "f1": mean("f1"), "type_acc": mean("type_acc")}},
              open(os.path.join(BASE, "out", "template_match_report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
if __name__ == "__main__":
    main()
