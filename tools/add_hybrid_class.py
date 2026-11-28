# -*- coding: utf-8 -*-
"""给 preannotate_core 增加混合推理类 HybridAnnotator。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "preannotate_core.py")
t = open(p, encoding="utf-8").read()
if "class HybridAnnotator" not in t:
    add = '''

class HybridAnnotator:
    """门控(有没有建筑) + embedding 最近邻(类型/背景) + 原型。"""

    def __init__(self, gate_path, emb_path, protos_path, meta_path, providers=None):
        import json
        import numpy as np
        import onnxruntime as ort
        providers = providers or ["CPUExecutionProvider"]
        self.gate = ort.InferenceSession(gate_path, providers=providers)
        self.emb = ort.InferenceSession(emb_path, providers=providers)
        meta = json.load(open(meta_path, encoding="utf-8"))
        z = np.load(protos_path)
        self.P = z["P"].astype(np.float32)
        self.PC = z["PC"].astype(np.int64)
        self.types = meta["types"]
        self.bg = int(meta.get("bg", len(self.types)))
        self.size = int(meta.get("size", 96))
        self.gate_th = float(meta.get("gate_th", 0.85))
        self.emb_th = float(meta.get("emb_th", 0.85))
        self.building_mask = self.PC != self.bg

    def _run(self, crops):
        import numpy as np
        x = np.stack(crops)[:, :, :, ::-1].astype(np.float32) / 255.0
        x = np.transpose(x, (0, 3, 1, 2))
        gp = self.gate.run(None, {self.gate.get_inputs()[0].name: x})[0]
        e = self.emb.run(None, {self.emb.get_inputs()[0].name: x})[0]
        eg = np.exp(gp - gp.max(1, keepdims=True)); pg = eg / eg.sum(1, keepdims=True)
        return pg[:, 1], e

    def detect(self, img, quad, gate_th=None, emb_th=None):
        import numpy as np
        gate_th = self.gate_th if gate_th is None else gate_th
        emb_th = self.emb_th if emb_th is None else emb_th
        cal = Calib.from_quad(np.float32(quad), n=44)
        cells = [(cx, cy) for cx in range(2, 42) for cy in range(2, 42)]
        cands = []
        B = 128
        for i in range(0, len(cells), B):
            cs = cells[i:i + B]
            crops = [_crop(img, cal, cx + .5, cy + .5, self.size) for (cx, cy) in cs]
            gprob, embs = self._run(crops)
            sim = embs @ self.P.T
            for k, (cx, cy) in enumerate(cs):
                if float(gprob[k]) < gate_th:
                    continue
                row = sim[k]
                bidx = int(row[self.building_mask].argmax()) if self.building_mask.any() else 0
                bmap = np.flatnonzero(self.building_mask)
                idx = int(bmap[bidx])
                bs = float(row[idx])
                bgmax = float(row[~self.building_mask].max()) if (~self.building_mask).any() else -1.0
                if bs < emb_th or bs <= bgmax:
                    continue
                cands.append((bs, int(self.PC[idx]), cx + .5, cy + .5))
        cands.sort(reverse=True)
        kept = []
        for c in cands:
            sz = int((STATS.get(self.types[c[1]]) or {}).get("size") or 2)
            ok = True
            for q in kept:
                qsz = int((STATS.get(self.types[q[1]]) or {}).get("size") or 2)
                if abs(c[2] - q[2]) + abs(c[3] - q[3]) < (sz + qsz) / 2.0 * 1.15:
                    ok = False
                    break
            if ok:
                kept.append(c)
        out = []
        for score, cls, cx, cy in kept:
            out.append({"type": self.types[cls], "score": round(score, 3), "center": [round(cx, 2), round(cy, 2)]})
        return out
'''
    t = t.rstrip() + add
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("HybridAnnotator appended")
else:
    print("already")
