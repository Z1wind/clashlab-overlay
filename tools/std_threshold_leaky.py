# -*- coding: utf-8 -*-
"""标准档阈值候选在 8 基准上的 leaky P/R（用于给标准档选更实用的点）。"""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
import cv2, numpy as np
from tools.preannotate_core import HybridAnnotator
DL = os.path.join(os.path.expanduser("~"), "Downloads")
paths = [os.path.join(DL, "annot_b01 (1).json"), os.path.join(DL, "annot_b02 (1).json")]
paths += [os.path.join(DL, "annot_b%02d.json" % i) for i in range(3, 9)]
pa = HybridAnnotator(os.path.join(BASE,"models","hybrid_gate.onnx"), os.path.join(BASE,"models","hybrid_emb.onnx"),
                     os.path.join(BASE,"models","hybrid_protos.npz"), os.path.join(BASE,"models","hybrid_meta.json"))
CFG = [(0.85,0.85),(0.80,0.85),(0.75,0.85),(0.70,0.85),(0.70,0.80),(0.75,0.80),(0.65,0.80)]
agg = {c: [] for c in CFG}
for path in paths:
    d = json.load(open(path, encoding="utf-8"))
    img = cv2.imdecode(np.fromfile(os.path.join(BASE, "android", "assets", d["image"]), np.uint8), cv2.IMREAD_COLOR)
    wn, hn = d["image_size"]; quad = [[u*wn, v*hn] for u, v in d["corners_norm"]]
    gt = [(b["type"], b["tile"][0]+.5, b["tile"][1]+.5) for b in d["buildings"]]
    for c in CFG:
        out = pa.detect(img, quad, gate_th=c[0], emb_th=c[1], phases=(0.0,))
        matched = set(); tp = tok = 0
        for o in out:
            best = None
            for gi,(tt,gx,gy) in enumerate(gt):
                if gi in matched: continue
                dd = abs(o["center"][0]-gx)+abs(o["center"][1]-gy)
                if dd < 1.6 and (best is None or dd < best[0]): best = (dd, gi)
            if best:
                matched.add(best[1]); tp += 1
                if o["type"] == gt[best[1]][0]: tok += 1
        agg[c].append((tp/max(1,len(out)), tp/len(gt), tok/max(1,tp), len(out)))
for c in CFG:
    rs = agg[c]
    m = lambda i: float(np.mean([r[i] for r in rs]))
    print("g=%.2f e=%.2f  P=%.3f R=%.3f F1=%.3f type=%.3f pred=%.0f" % (c[0], c[1], m(0), m(1), 2*m(0)*m(1)/max(1e-9,m(0)+m(1)), m(2), m(3)))
