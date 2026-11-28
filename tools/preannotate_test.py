# -*- coding: utf-8 -*-
"""测试预标注：在有标注的 b03 上跑，与 GT 对比（模型训练含此图，仅验证代码链路）。"""
import json, os, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import cv2, numpy as np
from tools.preannotate_core import PreAnnotator
d = json.load(open(os.path.join(os.path.expanduser("~"), "Downloads", "annot_b03.json"), encoding="utf-8"))
img = cv2.imdecode(np.fromfile(os.path.join(BASE, "android", "assets", d["image"]), np.uint8), cv2.IMREAD_COLOR)
wn, hn = d["image_size"]; quad = [[u * wn, v * hn] for u, v in d["corners_norm"]]
pa = PreAnnotator(os.path.join(BASE,"models","pipeline_gate.onnx"),
                  os.path.join(BASE,"models","pipeline_type.onnx"),
                  os.path.join(BASE,"models","pipeline_types.json"))
t0 = time.time(); out = pa.detect(img, quad); dt = time.time() - t0
gt = [(b["type"], b["tile"][0] + .5, b["tile"][1] + .5) for b in d["buildings"]]
matched = set(); tp = tok = 0
for o in out:
    best = None
    for gi, (t, gx, gy) in enumerate(gt):
        if gi in matched: continue
        dd = abs(o["center"][0]-gx) + abs(o["center"][1]-gy)
        if dd < 1.6 and (best is None or dd < best[0]): best = (dd, gi)
    if best:
        matched.add(best[1]); tp += 1
        if gt[best[1]][0] == o["type"]: tok += 1
print("pred", len(out), "gt", len(gt), "tp", tp,
      "prec %.3f" % (tp/max(1,len(out))), "recall %.3f" % (tp/max(1,len(gt))),
      "type_acc %.3f" % (tok/max(1,tp)), "耗时 %.2fs" % dt)
print("sample:", out[:5])
