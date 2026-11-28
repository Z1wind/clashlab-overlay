# -*- coding: utf-8 -*-
"""混合模型变体快速对比（在训练集上，leaky，只用于判断方向）：
A 基线 / B +TTA / C +位置精修 / D +占用后处理。
"""
import json, os, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import cv2, numpy as np
from clashlab.geo import Calib
from clashlab.assets import STATS
from tools.preannotate_core import HybridAnnotator
S = 96
def prep(path):
    d = json.load(open(path, encoding="utf-8"))
    img = cv2.imdecode(np.fromfile(os.path.join(BASE, "android", "assets", d["image"]), np.uint8), cv2.IMREAD_COLOR)
    wn, hn = d["image_size"]; quad = np.float32([[u*wn, v*hn] for u, v in d["corners_norm"]])
    return img, Calib.from_quad(quad, n=44), [(b["type"], b["tile"][0], b["tile"][1]) for b in d["buildings"]], quad
def crop(img, cal, cx, cy, size=S, shift=(0,0)):
    x0, y0 = cx - 1.5, cy - 1.5
    p = [cal.tile_to_px(x0,y0), cal.tile_to_px(x0+4,y0), cal.tile_to_px(x0+4,y0+4), cal.tile_to_px(x0,y0+4)]
    H = cv2.getPerspectiveTransform(np.float32(p), np.float32([[0,0],[size,0],[size,size],[0,size]]))
    c = cv2.warpPerspective(img, H, (size,size), flags=cv2.INTER_AREA)
    if shift != (0,0):
        M = np.float32([[1,0,shift[0]],[0,1,shift[1]]])
        c = cv2.warpAffine(c, M, (size,size), borderMode=cv2.BORDER_REFLECT)
    return c
def evaluate(pa, img, cal, gt, tta=False, refine=False, occupancy=False):
    cells = [(cx, cy) for cx in range(2,42) for cy in range(2,42)]
    feats = {}
    with_time = time.time()
    for i in range(0, len(cells), 128):
        cs = cells[i:i+128]
        if tta:
            allg, alle = [], []
            for sh in ((0,0),(4,0),(-4,0),(0,4),(0,-4)):
                crops = [crop(img, cal, cx, cy, shift=sh) for (cx,cy) in cs]
                g,e = pa._run(crops)
                allg.append(g); alle.append(e)
            g = np.mean(allg, 0); e = np.mean(alle, 0)
            e = e / np.maximum(np.linalg.norm(e, axis=1, keepdims=True), 1e-9)
        else:
            g, e = pa._run([crop(img, cal, cx, cy) for (cx,cy) in cs])
        for k, cell in enumerate(cs): feats[cell] = (float(g[k]), e[k])
    cands = []
    for cell, (gp, e) in feats.items():
        if gp < pa.gate_th: continue
        sim = pa.P @ e
        bmap = np.flatnonzero(pa.building_mask); idx = int(bmap[int(sim[bmap].argmax())])
        bs = float(sim[idx]); bgmax = float(sim[~pa.building_mask].max())
        if bs < pa.emb_th or bs <= bgmax: continue
        cands.append((bs, int(pa.PC[idx]), cell[0]+.5, cell[1]+.5))
    cands.sort(reverse=True)
    # 可选：位置精修（±0.25 tile，用门控概率）
    if refine and cands:
        newc = []
        for c in cands[:150]:
            best = (c[0], c[2], c[3])
            for dx in (-0.25, 0, 0.25):
                for dy in (-0.25, 0, 0.25):
                    if dx == 0 and dy == 0: continue
                    xx, yy = c[2]+dx, c[3]+dy
                    g, e = pa._run([crop(img, cal, xx, yy)])
                    if float(g[0]) > 0.85: best = (c[0], xx, yy); break
                else: continue
                break
            newc.append((c[0], c[1], best[1], best[2]))
        cands = newc
    kept = []
    occ = {}
    for c in cands:
        sz = int((STATS.get(pa.types[c[1]]) or {}).get("size") or 2)
        x, y = int(np.floor(c[2]-sz/2)), int(np.floor(c[3]-sz/2))
        if occupancy:
            cells_occ = [(x+i, y+j) for i in range(sz) for j in range(sz) if 0 <= x+i < 44 and 0 <= y+j < 44]
            if any(o in occ for o in cells_occ): continue
            for o in cells_occ: occ[o] = True
        ok = True
        for q in kept:
            qsz = int((STATS.get(pa.types[q[1]]) or {}).get("size") or 2)
            if abs(c[2]-q[2]) + abs(c[3]-q[3]) < (sz+qsz)/2.0*1.15: ok = False; break
        if ok: kept.append(c)
    matched = set(); tp = tok = 0; errs = []
    for (s, cls, cx, cy) in kept:
        best = None
        for gi,(tt,gx,gy) in enumerate(gt):
            if gi in matched: continue
            d = abs(cx-(gx+.5))+abs(cy-(gy+.5))
            if d < 1.6 and (best is None or d < best[0]): best = (d, gi)
        if best:
            matched.add(best[1]); tp += 1; errs.append(best[0])
            if pa.types[cls] == gt[best[1]][0]: tok += 1
    n = len(gt)
    return {"pred": len(kept), "tp": tp, "prec": tp/max(1,len(kept)), "recall": tp/n,
            "f1": 2*(tp/max(1,len(kept)))*(tp/n)/max(1e-9,(tp/max(1,len(kept)))+(tp/n)),
            "type": tok/max(1,tp), "mean_err": float(np.mean(errs)) if errs else None,
            "ms": int((time.time()-with_time)*1000)}
def main():
    pa = HybridAnnotator(os.path.join(BASE,"models","hybrid_gate.onnx"),
                         os.path.join(BASE,"models","hybrid_emb.onnx"),
                         os.path.join(BASE,"models","hybrid_protos.npz"),
                         os.path.join(BASE,"models","hybrid_meta.json"))
    paths = [os.path.join(os.path.expanduser("~"), "Downloads", "annot_b01 (1).json"),
             os.path.join(os.path.expanduser("~"), "Downloads", "annot_b02 (1).json")]
    paths += [os.path.join(os.path.expanduser("~"), "Downloads", "annot_b%02d.json" % i) for i in range(3, 9)]
    variants = [("A_base", dict()), ("B_tta", dict(tta=True)), ("C_refine", dict(refine=True)),
                ("D_occ", dict(occupancy=True)), ("E_tta_occ", dict(tta=True, occupancy=True)),
                ("F_tta_refine_occ", dict(tta=True, refine=True, occupancy=True))]
    agg = {n: [] for n,_ in variants}
    for p in paths:
        img, cal, gt, quad = prep(p)
        for name, kw in variants:
            r = evaluate(pa, img, cal, gt, **kw)
            agg[name].append(r)
        print("done", os.path.basename(p), flush=True)
    for name, _ in variants:
        rs = agg[name]
        m = lambda k: float(np.mean([r[k] for r in rs]))
        print("VARIANT %-18s prec=%.3f recall=%.3f f1=%.3f type=%.3f err=%.2f ms=%d" % (
            name, m("prec"), m("recall"), m("f1"), m("type"), m("mean_err") or 0, m("ms")), flush=True)
    json.dump({name: agg[name] for name,_ in variants}, open(os.path.join(BASE,"out","hybrid_variants.json"), "w", encoding="utf-8"), indent=1)
if __name__ == "__main__":
    main()
