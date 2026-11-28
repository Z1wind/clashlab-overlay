# -*- coding: utf-8 -*-
"""预标注核心：门控+类型 ONNX 推理，输入图像与四角，输出建筑列表。"""
import json
import os
import numpy as np
import cv2
from clashlab.geo import Calib
from clashlab.assets import STATS

S = 96

def _crop(img, cal, tx, ty, size):
    x0, y0 = tx - 1.5, ty - 1.5
    p = [cal.tile_to_px(x0, y0), cal.tile_to_px(x0 + 4, y0),
         cal.tile_to_px(x0 + 4, y0 + 4), cal.tile_to_px(x0, y0 + 4)]
    H = cv2.getPerspectiveTransform(np.float32(p), np.float32([[0, 0], [size, 0], [size, size], [0, size]]))
    return cv2.warpPerspective(img, H, (size, size), flags=cv2.INTER_AREA)

class PreAnnotator:
    def __init__(self, gate_path, type_path, types_path, providers=None):
        import onnxruntime as ort
        providers = providers or ["CPUExecutionProvider"]
        self.gate = ort.InferenceSession(gate_path, providers=providers)
        self.tnet = ort.InferenceSession(type_path, providers=providers)
        meta = json.load(open(types_path, encoding="utf-8"))
        self.types = meta["types"]
        self.size = int(meta.get("size", 96))
        self.gate_in = self.gate.get_inputs()[0].name
        self.type_in = self.tnet.get_inputs()[0].name

    def _run_batch(self, crops):
        x = np.stack(crops)[:, :, :, ::-1].astype(np.float32) / 255.0
        x = np.transpose(x, (0, 3, 1, 2))
        g = self.gate.run(None, {self.gate_in: x})[0]
        t = self.tnet.run(None, {self.type_in: x})[0]
        eg = np.exp(g - g.max(1, keepdims=True)); pg = eg / eg.sum(1, keepdims=True)
        et = np.exp(t - t.max(1, keepdims=True)); pt = et / et.sum(1, keepdims=True)
        return pg[:, 1], pt

    def detect(self, img, quad, gate_th=0.5, score_th=0.5):
        cal = Calib.from_quad(np.float32(quad), n=44)
        cells = [(cx, cy) for cx in range(2, 42) for cy in range(2, 42)]
        cands = []
        B = 128
        for i in range(0, len(cells), B):
            cs = cells[i:i + B]
            crops = [_crop(img, cal, cx + .5, cy + .5, self.size) for (cx, cy) in cs]
            gprob, tprob = self._run_batch(crops)
            for k, (cx, cy) in enumerate(cs):
                if float(gprob[k]) < gate_th:
                    continue
                cls = int(tprob[k].argmax())
                score = float(gprob[k]) * float(tprob[k].max())
                if score < score_th:
                    continue
                cands.append((score, cls, cx + .5, cy + .5))
        cands.sort(reverse=True)
        kept = []
        for c in cands:
            sz = int((STATS.get(self.types[c[1]]) or {}).get("size") or 2)
            ok = True
            for q in kept:
                qsz = int((STATS.get(self.types[q[1]]) or {}).get("size") or 2)
                sep = (sz + qsz) / 2.0
                if abs(c[2] - q[2]) + abs(c[3] - q[3]) < sep * 1.15:
                    ok = False
                    break
            if ok:
                kept.append(c)
        out = []
        for score, cls, cx, cy in kept:
            out.append({"type": self.types[cls], "score": round(score, 3), "center": [round(cx, 2), round(cy, 2)]})
        return out
