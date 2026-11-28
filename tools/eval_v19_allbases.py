# -*- coding: utf-8 -*-
"""v1.9 三模式在全部 8 基准上的表现（leaky，交付前一致性检查）。"""
import json, os, sys, time
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
CFG = {"standard": (0.85, 0.85, (0.0,)), "recall": (0.70, 0.70, (0.0,)), "precise": (0.90, 0.90, (0.0, 0.5))}
agg = {m: [] for m in CFG}
for path in paths:
    d = json.load(open(path, encoding="utf-8"))
    img = cv2.imdecode(np.fromfile(os.path.join(BASE, "android", "assets", d["image"]), np.uint8), cv2.IMREAD_COLOR)
    wn, hn = d["image_size"]; quad = [[u*wn, v*hn] for u, v in d["corners_norm"]]
    gt = [(b["type"], b["tile"][0]+.5, b["tile"][1]+.5) for b in d["buildings"]]
    row = []
    for m, (g, e, ph) in CFG.items():
        t0 = time.time(); out = pa.detect(img, quad, gate_th=g, emb_th=e, phases=ph); dt = int((time.time()-t0)*1000)
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
        p = tp/max(1,len(out)); r = tp/len(gt)
        agg[m].append({"p": p, "r": r, "t": tok/max(1,tp), "n": len(out), "gt": len(gt), "ms": dt})
        row.append("%s n=%d P=%.2f R=%.2f T=%.2f %dms" % (m, len(out), p, r, tok/max(1,tp), dt))
    print("%-22s %s" % (os.path.basename(path), " | ".join(row)), flush=True)
print()
for m, rs in agg.items():
    mean = lambda k: float(np.mean([x[k] for x in rs]))
    print("MODE %-8s P=%.3f R=%.3f type=%.3f 平均栋数=%.0f 平均耗时=%dms" % (m, mean("p"), mean("r"), mean("t"), mean("n"), mean("ms")))
