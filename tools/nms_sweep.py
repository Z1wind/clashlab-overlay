# -*- coding: utf-8 -*-
"""NMS 去重系数扫描（leaky，仅看方向）。"""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import cv2, numpy as np, torch
from clashlab.geo import Calib
from clashlab.assets import STATS
from tools.preannotate_core import HybridAnnotator
DL = os.path.join(os.path.expanduser("~"), "Downloads")
paths = [os.path.join(DL, "annot_b01 (1).json"), os.path.join(DL, "annot_b02 (1).json")]
paths += [os.path.join(DL, "annot_b%02d.json" % i) for i in range(3, 9)]
pa = HybridAnnotator(os.path.join(BASE,"models","hybrid_gate.onnx"), os.path.join(BASE,"models","hybrid_emb.onnx"),
                     os.path.join(BASE,"models","hybrid_protos.npz"), os.path.join(BASE,"models","hybrid_meta.json"))
def raw_candidates(img, quad, gth, eth):
    cal = Calib.from_quad(np.float32(quad), n=44)
    cells = [(cx, cy) for cx in range(2, 42) for cy in range(2, 42)]
    out = []
    for i in range(0, len(cells), 128):
        cs = cells[i:i+128]
        crops = []
        for (cx, cy) in cs:
            x0, y0 = cx-1.5, cy-1.5
            p = [cal.tile_to_px(x0,y0), cal.tile_to_px(x0+4,y0), cal.tile_to_px(x0+4,y0+4), cal.tile_to_px(x0,y0+4)]
            H = cv2.getPerspectiveTransform(np.float32(p), np.float32([[0,0],[96,0],[96,96],[0,96]]))
            crops.append(cv2.warpPerspective(img, H, (96,96), flags=cv2.INTER_AREA))
        gp, e = pa._run(crops)
        sim = e @ pa.P.T
        bmap = np.flatnonzero(pa.building_mask); bgmap = np.flatnonzero(~pa.building_mask)
        best = sim[:, bmap].max(1); bi = sim[:, bmap].argmax(1); bgm = sim[:, bgmap].max(1)
        for k, (cx, cy) in enumerate(cs):
            if gp[k] < gth or best[k] < eth or best[k] <= bgm[k]: continue
            out.append((float(best[k]), int(pa.PC[bmap[bi[k]]]), cx+.5, cy+.5))
    out.sort(reverse=True)
    return out
def evaluate(cands, gt, factor, tol=1.6):
    kept = []
    for c in cands:
        sz = int((STATS.get(pa.types[c[1]]) or {}).get("size") or 2)
        ok = True
        for q in kept:
            qsz = int((STATS.get(pa.types[q[1]]) or {}).get("size") or 2)
            if abs(c[2]-q[2]) + abs(c[3]-q[3]) < (sz+qsz)/2.0*factor: ok = False; break
        if ok: kept.append(c)
    matched = set(); tp = tok = 0
    for (s, cls, cx, cy) in kept:
        bb = None
        for gi,(tt,gx,gy) in enumerate(gt):
            if gi in matched: continue
            dd = abs(cx-gx)+abs(cy-gy)
            if dd < tol and (bb is None or dd < bb[0]): bb = (dd, gi)
        if bb:
            matched.add(bb[1]); tp += 1
            if pa.types[cls] == gt[bb[1]][0]: tok += 1
    prec = tp/max(1,len(kept)); rec = tp/max(1,len(gt))
    return prec, rec, 2*prec*rec/max(1e-9,prec+rec), tok/max(1,tp), len(kept)
res = {}
for p in paths:
    d = json.load(open(p, encoding="utf-8"))
    img = cv2.imdecode(np.fromfile(os.path.join(BASE, "android", "assets", d["image"]), np.uint8), cv2.IMREAD_COLOR)
    wn, hn = d["image_size"]; quad = [[u*wn, v*hn] for u, v in d["corners_norm"]]
    gt = [(b["type"], b["tile"][0]+.5, b["tile"][1]+.5) for b in d["buildings"]]
    cands = raw_candidates(img, quad, 0.70, 0.85)
    for f in (0.70, 0.85, 1.00, 1.15, 1.30):
        r = evaluate(cands, gt, f)
        res.setdefault(f, []).append(r)
    print("done", os.path.basename(p), flush=True)
for f, rs in sorted(res.items()):
    m = lambda i: float(np.mean([r[i] for r in rs]))
    print("NMS %.2f: P=%.3f R=%.3f F1=%.3f type=%.3f pred=%.0f" % (f, m(0), m(1), m(2), m(3), m(4)))
