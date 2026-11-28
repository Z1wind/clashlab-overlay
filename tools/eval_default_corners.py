# -*- coding: utf-8 -*-
"""用平均四角（默认四角）代替手工四角，测预标注精度损失。"""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import cv2, numpy as np
from tools.preannotate_core import HybridAnnotator
DL = os.path.join(os.path.expanduser("~"), "Downloads")
paths = [os.path.join(DL, "annot_b01 (1).json"), os.path.join(DL, "annot_b02 (1).json")]
paths += [os.path.join(DL, "annot_b%02d.json" % i) for i in range(3, 9)]
DEFAULT = np.float32([[0.498, -0.100], [0.871, 0.502], [0.500, 1.105], [0.123, 0.505]])
pa = HybridAnnotator(os.path.join(BASE,"models","hybrid_gate.onnx"), os.path.join(BASE,"models","hybrid_emb.onnx"),
                     os.path.join(BASE,"models","hybrid_protos.npz"), os.path.join(BASE,"models","hybrid_meta.json"))
def ev(img, quad, gt, gth, eth):
    out = pa.detect(img, quad, gate_th=gth, emb_th=eth)
    matched = set(); tp = tok = 0
    for o in out:
        best = None
        for gi,(tt,gx,gy) in enumerate(gt):
            if gi in matched: continue
            dd = abs(o["center"][0]-gx) + abs(o["center"][1]-gy)
            if dd < 1.6 and (best is None or dd < best[0]): best = (dd, gi)
        if best:
            matched.add(best[1]); tp += 1
            if o["type"] == gt[best[1]][0]: tok += 1
    return len(out), tp, tp/max(1,len(out)), tp/len(gt), tok/max(1,tp)
rows = []
for p in paths:
    d = json.load(open(p, encoding="utf-8"))
    img = cv2.imdecode(np.fromfile(os.path.join(BASE, "android", "assets", d["image"]), np.uint8), cv2.IMREAD_COLOR)
    wn, hn = d["image_size"]
    real = np.float32([[u*wn, v*hn] for u, v in d["corners_norm"]])
    dflt = np.float32([[u*wn, v*hn] for u, v in DEFAULT])
    gt = [(b["type"], b["tile"][0]+.5, b["tile"][1]+.5) for b in d["buildings"]]
    a = ev(img, real, gt, 0.85, 0.85)
    b = ev(img, dflt, gt, 0.85, 0.85)
    rows.append((a, b))
    print("%-20s real: pred=%d tp=%d P=%.2f R=%.2f T=%.2f | default: pred=%d tp=%d P=%.2f R=%.2f T=%.2f" % (
        os.path.basename(p), a[0], a[1], a[2], a[3], a[4], b[0], b[1], b[2], b[3], b[4]))
m = lambda k, i: float(np.mean([r[i][k] for r in rows]))
print("\nMEAN real   P=%.3f R=%.3f T=%.3f" % (m(2,0), m(3,0), m(4,0)))
print("MEAN default P=%.3f R=%.3f T=%.3f" % (m(2,1), m(3,1), m(4,1)))
