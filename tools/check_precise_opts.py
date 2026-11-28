# -*- coding: utf-8 -*-
import json, os, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
import cv2, numpy as np
from tools.preannotate_core import HybridAnnotator
d = json.load(open(os.path.join(os.path.expanduser("~"), "Downloads", "annot_b03.json"), encoding="utf-8"))
img = cv2.imdecode(np.fromfile(os.path.join(BASE, "android", "assets", d["image"]), np.uint8), cv2.IMREAD_COLOR)
wn, hn = d["image_size"]; quad = [[u*wn, v*hn] for u, v in d["corners_norm"]]
gt = [(b["type"], b["tile"][0]+.5, b["tile"][1]+.5) for b in d["buildings"]]
pa = HybridAnnotator(os.path.join(BASE,"models","hybrid_gate.onnx"), os.path.join(BASE,"models","hybrid_emb.onnx"),
                     os.path.join(BASE,"models","hybrid_protos.npz"), os.path.join(BASE,"models","hybrid_meta.json"))
def ev(name, g, e, phases):
    t0 = time.time(); out = pa.detect(img, quad, gate_th=g, emb_th=e, phases=phases); dt = int((time.time()-t0)*1000)
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
    print("%-22s pred=%-3d tp=%-2d P=%.3f R=%.3f type=%.3f ms=%d" % (name, len(out), tp, tp/max(1,len(out)), tp/len(gt), tok/max(1,tp), dt))
ev("std(0.85/0.85,1ph)", 0.85, 0.85, (0.0,))
ev("precise A(.90/.90,2ph)", 0.90, 0.90, (0.0, 0.5))
ev("precise B(.92/.90,2ph)", 0.92, 0.90, (0.0, 0.5))
ev("precise C(.92/.92,2ph)", 0.92, 0.92, (0.0, 0.5))
