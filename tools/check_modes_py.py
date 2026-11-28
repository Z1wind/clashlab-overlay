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
pa = HybridAnnotator(os.path.join(BASE,"models","hybrid_gate.onnx"), os.path.join(BASE,"models","hybrid_emb.onnx"),
                     os.path.join(BASE,"models","hybrid_protos.npz"), os.path.join(BASE,"models","hybrid_meta.json"))
cfg = {"standard": (0.85, 0.85, (0.0,)), "recall": (0.70, 0.70, (0.0,)), "precise": (0.90, 0.85, (0.0, 0.5))}
for m, c in cfg.items():
    t0 = time.time(); out = pa.detect(img, quad, gate_th=c[0], emb_th=c[1], phases=c[2]); dt = int((time.time()-t0)*1000)
    print(m, "n=", len(out), "ms=", dt)
