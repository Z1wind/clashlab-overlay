# -*- coding: utf-8 -*-
"""按建筑类型统计 v1.9 标准模式的漏检/误判（leaky 8 基准），找出最该补数据的类型。"""
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
stat = {}
confuse = {}
for path in paths:
    d = json.load(open(path, encoding="utf-8"))
    img = cv2.imdecode(np.fromfile(os.path.join(BASE, "android", "assets", d["image"]), np.uint8), cv2.IMREAD_COLOR)
    wn, hn = d["image_size"]; quad = [[u*wn, v*hn] for u, v in d["corners_norm"]]
    gt = [(b["type"], b["tile"][0]+.5, b["tile"][1]+.5) for b in d["buildings"]]
    out = pa.detect(img, quad, gate_th=0.85, emb_th=0.85, phases=(0.0,))
    used = set()
    for o in out:
        best = None
        for gi,(tt,gx,gy) in enumerate(gt):
            if gi in used: continue
            dd = abs(o["center"][0]-gx)+abs(o["center"][1]-gy)
            if dd < 1.6 and (best is None or dd < best[0]): best = (dd, gi)
        if best:
            used.add(best[1]); t = gt[best[1]][0]
            s = stat.setdefault(t, {"n":0,"tp":0,"ok":0}); s["n"] += 1; s["tp"] += 1
            if o["type"] == t: s["ok"] += 1
            else: confuse[(t, o["type"])] = confuse.get((t, o["type"]), 0) + 1
    for gi,(t,gx,gy) in enumerate(gt):
        if gi not in used: stat.setdefault(t, {"n":0,"tp":0,"ok":0})["n"] += 1
rows = [(t, s["n"], s["tp"], s["tp"]/max(1,s["n"]), s["ok"]/max(1,s["tp"])) for t,s in stat.items()]
rows = [r for r in rows if r[1] >= 3]
rows.sort(key=lambda r: (r[3], r[4]))
print("最差类型（召回/类型）：")
for t,n,tp,rec,tacc in rows[:14]:
    print("  %-22s n=%-3d 召回=%.2f 类型=%.2f" % (t, n, rec, tacc))
print("\n最常见类型混淆：")
for (a,b),c in sorted(confuse.items(), key=lambda kv:-kv[1])[:10]:
    print("  %-20s -> %-20s x%d" % (a, b, c))
