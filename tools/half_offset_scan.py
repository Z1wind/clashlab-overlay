# -*- coding: utf-8 -*-
"""半格相位扫描：整数格 + 半格候选合并，看能否提升召回（leaky 8 基准）。"""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import cv2, numpy as np
from clashlab.geo import Calib
from clashlab.assets import STATS
from tools.preannotate_core import HybridAnnotator
DL = os.path.join(os.path.expanduser("~"), "Downloads")
paths = [os.path.join(DL, "annot_b01 (1).json"), os.path.join(DL, "annot_b02 (1).json")]
paths += [os.path.join(DL, "annot_b%02d.json" % i) for i in range(3, 9)]
pa = HybridAnnotator(os.path.join(BASE,"models","hybrid_gate.onnx"), os.path.join(BASE,"models","hybrid_emb.onnx"),
                     os.path.join(BASE,"models","hybrid_protos.npz"), os.path.join(BASE,"models","hybrid_meta.json"))
def cells(phase):
    off = 0.0 if phase == 0 else 0.5
    return [(x + off, y + off) for x in range(2, 42) for y in range(2, 42)]
def cands_for(img, cal, cs, gth, eth):
    out = []
    B = 128
    for i in range(0, len(cs), B):
        sub = cs[i:i+B]
        crops = []
        for (cx, cy) in sub:
            x0, y0 = cx-1.5, cy-1.5
            p = [cal.tile_to_px(x0,y0), cal.tile_to_px(x0+4,y0), cal.tile_to_px(x0+4,y0+4), cal.tile_to_px(x0,y0+4)]
            H = cv2.getPerspectiveTransform(np.float32(p), np.float32([[0,0],[96,0],[96,96],[0,96]]))
            crops.append(cv2.warpPerspective(img, H, (96,96), flags=cv2.INTER_AREA))
        gp, e = pa._run(crops)
        sim = e @ pa.P.T
        bmap = np.flatnonzero(pa.building_mask); bgmap = np.flatnonzero(~pa.building_mask)
        bb = sim[:, bmap].max(1); bi = sim[:, bmap].argmax(1); bgm = sim[:, bgmap].max(1)
        for k, (cx, cy) in enumerate(sub):
            if gp[k] < gth or bb[k] < eth or bb[k] <= bgm[k]: continue
            out.append((float(bb[k]), int(pa.PC[bmap[bi[k]]]), cx+.5, cy+.5))
    return out
def evaluate(cands, gt):
    cands = sorted(cands, reverse=True)
    kept = []
    for c in cands:
        sz = int((STATS.get(pa.types[c[1]]) or {}).get("size") or 2)
        ok = True
        for q in kept:
            qsz = int((STATS.get(pa.types[q[1]]) or {}).get("size") or 2)
            if abs(c[2]-q[2]) + abs(c[3]-q[3]) < (sz+qsz)/2.0*1.15: ok = False; break
        if ok: kept.append(c)
    matched = set(); tp = tok = 0
    for (s, cls, cx, cy) in kept:
        best = None
        for gi,(tt,gx,gy) in enumerate(gt):
            if gi in matched: continue
            dd = abs(cx-gx)+abs(cy-gy)
            if dd < 1.6 and (best is None or dd < best[0]): best = (dd, gi)
        if best:
            matched.add(best[1]); tp += 1
            if pa.types[cls] == gt[best[1]][0]: tok += 1
    p = tp/max(1,len(kept)); r = tp/max(1,len(gt))
    return p, r, 2*p*r/max(1e-9,p+r), tok/max(1,tp), len(kept)
res = {"int": [], "half": [], "both": []}
for path in paths:
    d = json.load(open(path, encoding="utf-8"))
    img = cv2.imdecode(np.fromfile(os.path.join(BASE, "android", "assets", d["image"]), np.uint8), cv2.IMREAD_COLOR)
    wn, hn = d["image_size"]; quad = np.float32([[u*wn, v*hn] for u, v in d["corners_norm"]])
    cal = Calib.from_quad(quad, n=44)
    gt = [(b["type"], b["tile"][0]+.5, b["tile"][1]+.5) for b in d["buildings"]]
    ci = cands_for(img, cal, cells(0), 0.85, 0.85)
    ch = cands_for(img, cal, cells(1), 0.85, 0.85)
    res["int"].append(evaluate(ci, gt))
    res["half"].append(evaluate(ch, gt))
    res["both"].append(evaluate(ci + ch, gt))
    print("done", os.path.basename(path), flush=True)
for k, rs in res.items():
    m = lambda i: float(np.mean([r[i] for r in rs]))
    print("%-5s P=%.3f R=%.3f F1=%.3f type=%.3f pred=%.0f" % (k, m(0), m(1), m(2), m(3), m(4)))
