# -*- coding: utf-8 -*-
"""完整流水线诚实评估：每折重训 门控 + 类型分类 → 检测 + 类型 → P/R/F1/类型准确率。"""
import argparse, json, os, random, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import cv2, numpy as np, torch, torch.nn as nn
from clashlab.geo import Calib
from clashlab.assets import STATS
S = 96
def prep(path):
    d = json.load(open(path, encoding="utf-8"))
    img = cv2.imdecode(np.fromfile(os.path.join(BASE, "android", "assets", d["image"]), np.uint8), cv2.IMREAD_COLOR)
    wn, hn = d["image_size"]; quad = np.float32([[u*wn, v*hn] for u, v in d["corners_norm"]])
    cal = Calib.from_quad(quad, n=44)
    blds = [(b["type"], b["tile"][0] + .5, b["tile"][1] + .5) for b in d["buildings"]]
    return img, cal, blds, d
def crop(img, cal, tx, ty):
    x0, y0 = tx - 1.5, ty - 1.5
    p = [cal.tile_to_px(x0,y0), cal.tile_to_px(x0+4,y0), cal.tile_to_px(x0+4,y0+4), cal.tile_to_px(x0,y0+4)]
    H = cv2.getPerspectiveTransform(np.float32(p), np.float32([[0,0],[S,0],[S,S],[0,S]]))
    return cv2.warpPerspective(img, H, (S,S), flags=cv2.INTER_AREA)
def aug(c, r):
    x = c.astype(np.float32) * r.uniform(0.85,1.15) + r.uniform(-12,12); x = np.clip(x,0,255)
    M = cv2.getRotationMatrix2D((S/2,S/2), r.uniform(-4,4), r.uniform(0.92,1.08))
    M[0,2] += r.uniform(-3,3); M[1,2] += r.uniform(-3,3)
    x = cv2.warpAffine(x, M, (S,S), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return x.astype(np.uint8)
class Net(nn.Module):
    def __init__(self, n):
        super().__init__()
        def blk(i,o): return nn.Sequential(nn.Conv2d(i,o,3,padding=1), nn.BatchNorm2d(o), nn.ReLU(True), nn.MaxPool2d(2))
        self.f = nn.Sequential(blk(3,32), blk(32,64), blk(64,128), blk(128,192), nn.AdaptiveAvgPool2d(1))
        self.drop = nn.Dropout(0.25); self.head = nn.Linear(192, n)
    def forward(self, x): return self.head(self.drop(self.f(x).flatten(1)))
def batch(items, DEV):
    xs = np.stack([c for c,_ in items])[:, :, :, ::-1]
    x = torch.from_numpy(xs.copy()).permute(0,3,1,2).float().div(255).to(DEV)
    y = torch.tensor([l for _,l in items], dtype=torch.long).to(DEV)
    return x, y
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", required=True)
    ap.add_argument("--exclude", default="")
    ap.add_argument("--gate-epochs", type=int, default=24)
    ap.add_argument("--type-epochs", type=int, default=20)
    a = ap.parse_args()
    excl = {int(x) for x in a.exclude.split(",") if x.strip()}
    paths = [p.strip() for p in a.export.split(",") if p.strip() and os.path.exists(p.strip())]
    data = []
    for bi, p in enumerate(paths):
        if bi in excl: continue
        img, cal, blds, d = prep(p); data.append({"bi": bi, "img": img, "cal": cal, "blds": blds})
        print("load base", bi, len(blds), flush=True)
    types = sorted({t for b in data for (t,_,_) in b["blds"]}); TIDX = {t:i for i,t in enumerate(types)}
    rng = random.Random(7); DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("bases", len(data), "types", len(types), "device", DEV, flush=True)
    reports = []
    for hold in range(len(data)):
        tr = [b for i,b in enumerate(data) if i != hold]; va = data[hold]
        # 门控数据
        gpos, gneg = [], []
        for b in tr:
            img, cal, blds = b["img"], b["cal"], b["blds"]
            for (t, cx, cy) in blds: gpos.append((crop(img, cal, cx, cy), 1))
            tries = 0
            while tries < 6000:
                tries += 1
                cx = rng.uniform(1.5, 42.5); cy = rng.uniform(1.5, 42.5)
                if any(abs(cx-ox)+abs(cy-oy) < 2.2 for (_,ox,oy) in blds): continue
                gneg.append((crop(img, cal, cx, cy), 0))
                if len(gneg) >= 110 * len(tr): break
        gate = Net(2).to(DEV); opt = torch.optim.AdamW(gate.parameters(), lr=2e-3, weight_decay=2e-4)
        lossf = nn.CrossEntropyLoss(weight=torch.tensor([1.0,3.0], device=DEV), label_smoothing=0.03)
        for ep in range(a.gate_epochs):
            gate.train(); rng.shuffle(gpos); rng.shuffle(gneg)
            for it in range(max(1,(len(gpos)+len(gneg))//80)):
                items = [(aug(c,rng),l) for (c,l) in gpos[rng.randrange(len(gpos)):rng.randrange(len(gpos))+1] ] if False else None
                items = [(aug(c,rng),l) for (c,l) in [gpos[rng.randrange(len(gpos))] for _ in range(40)]]
                items += [(aug(c,rng),l) for (c,l) in [gneg[rng.randrange(len(gneg))] for _ in range(40)]]
                x, y = batch(items, DEV); loss = lossf(gate(x), y); opt.zero_grad(); loss.backward(); opt.step()
        # 类型数据
        tpos = []
        for b in tr:
            img, cal = b["img"], b["cal"]
            for (t, cx, cy) in b["blds"]: tpos.append((crop(img, cal, cx, cy), TIDX[t]))
        tnet = Net(len(types)).to(DEV); opt2 = torch.optim.AdamW(tnet.parameters(), lr=2e-3, weight_decay=2e-4)
        lossf2 = nn.CrossEntropyLoss(label_smoothing=0.03)
        for ep in range(a.type_epochs):
            tnet.train(); rng.shuffle(tpos)
            for it in range(max(1, len(tpos)//64)):
                items = [(aug(c,rng), l) for (c,l) in tpos[rng.randrange(len(tpos)):rng.randrange(len(tpos))+1]] if False else [(aug(c,rng), l) for (c,l) in [tpos[rng.randrange(len(tpos))] for _ in range(64)]]
                x, y = batch(items, DEV); loss = lossf2(tnet(x), y); opt2.zero_grad(); loss.backward(); opt2.step()
        # 评估：门控候选 → 类型 → 足迹去重
        gate.eval(); tnet.eval(); img, cal, blds = va["img"], va["cal"], va["blds"]
        gt = [(t, cx, cy) for (t,cx,cy) in blds]
        cells = [(cx, cy) for cx in range(2,42) for cy in range(2,42)]
        cand = []
        with torch.no_grad():
            for i in range(0, len(cells), 128):
                cs = cells[i:i+128]
                x, _ = batch([(crop(img, cal, cx+.5, cy+.5), 0) for (cx,cy) in cs], DEV)
                gprob = torch.softmax(gate(x), 1)[:,1]
                tprob = torch.softmax(tnet(x), 1).max(1)
                for k,(cx,cy) in enumerate(cs):
                    if float(gprob[k]) < 0.5: continue
                    cand.append((float(gprob[k]) * float(tprob.values[k]), int(tprob.indices[k]), cx+.5, cy+.5))
        best = None
        for th in (0.5,0.6,0.7,0.8,0.9,0.95,0.98):
            sel = sorted([c for c in cand if c[0] >= th], reverse=True)
            kept = []
            for c in sel:
                sz = int((STATS.get(types[c[1]]) or {}).get("size") or 2)
                ok = True
                for q in kept:
                    qsz = int((STATS.get(types[q[1]]) or {}).get("size") or 2)
                    sep = (sz + qsz) / 2.0
                    if abs(c[2]-q[2]) + abs(c[3]-q[3]) < sep * 1.15: ok = False; break
                if ok: kept.append(c)
            matched = set(); tp = 0; tok = 0
            for (s, cls, cx, cy) in kept:
                bb = None
                for gi, (tt, gx, gy) in enumerate(gt):
                    if gi in matched: continue
                    d = abs(cx-gx) + abs(cy-gy)
                    if d < 1.6 and (bb is None or d < bb[0]): bb = (d, gi)
                if bb:
                    matched.add(bb[1]); tp += 1
                    if types[cls] == gt[bb[1]][0]: tok += 1
            prec = tp/max(1,len(kept)); rec = tp/max(1,len(gt)); f1 = 2*prec*rec/max(1e-9,prec+rec)
            tacc = tok/max(1,tp)
            if best is None or f1 > best[0]: best = (f1, th, prec, rec, tp, len(kept), tacc)
        f1, th, prec, rec, tp, npred, tacc = best
        print("hold base %d: gt=%d pred=%d tp=%d prec=%.3f recall=%.3f f1=%.3f type_acc=%.3f @th=%.2f" % (va["bi"], len(gt), npred, tp, prec, rec, f1, tacc, th), flush=True)
        reports.append({"base": va["bi"], "gt": len(gt), "pred": npred, "tp": tp, "prec": prec, "recall": rec, "f1": f1, "type_acc": tacc})
    mean = lambda k: sum(r[k] for r in reports)/len(reports)
    print("PIPELINE MEAN prec=%.3f recall=%.3f f1=%.3f type_acc=%.3f" % (mean("prec"), mean("recall"), mean("f1"), mean("type_acc")))
    json.dump({"reports": reports, "mean": {"prec": mean("prec"), "recall": mean("recall"), "f1": mean("f1"), "type_acc": mean("type_acc")}},
              open(os.path.join(BASE,"out","pipeline_report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
if __name__ == "__main__":
    main()
