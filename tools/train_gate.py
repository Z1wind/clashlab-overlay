# -*- coding: utf-8 -*-
"""两阶段第一步：建筑存在性门控（背景 vs 建筑），留一基验证位置 P/R。

用法: python tools/train_gate.py --export a,b --epochs 30
"""
import argparse, json, os, random, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import cv2, numpy as np, torch, torch.nn as nn
from tools.apk_export_to_dataset import load_export
from clashlab.geo import Calib
S = 96
def prep(path):
    d = json.load(open(path, encoding="utf-8"))
    img = cv2.imdecode(np.fromfile(os.path.join(BASE, "android", "assets", d["image"]), np.uint8), cv2.IMREAD_COLOR)
    wn, hn = d["image_size"]; quad = np.float32([[u*wn, v*hn] for u, v in d["corners_norm"]])
    cal = Calib.from_quad(quad, n=44)
    centers = []
    for b in d["buildings"]:
        x, y = b["tile"]; centers.append((x + .5, y + .5, b["type"]))
    return img, cal, centers
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
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", required=True)
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--exclude", default="")
    ap.add_argument("--out", default=os.path.join(BASE,"models","gate.pt"))
    ap.add_argument("--report", default=os.path.join(BASE,"out","gate_report.json"))
    a = ap.parse_args()
    excl = {int(x) for x in a.exclude.split(",") if x.strip()}
    paths = [p.strip() for p in a.export.split(",") if p.strip() and os.path.exists(p.strip())]
    data = []
    for bi, p in enumerate(paths):
        if bi in excl: continue
        img, cal, centers = prep(p); data.append({"bi": bi, "img": img, "cal": cal, "centers": centers})
        print("load", bi, len(centers), flush=True)
    rng = random.Random(7); DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    def samples(b):
        img, cal, centers = b["img"], b["cal"], b["centers"]
        pos = [(crop(img, cal, cx, cy), 1) for (cx, cy, _t) in centers]
        neg = []; tries = 0
        while len(neg) < 120 and tries < 6000:
            tries += 1
            cx = rng.uniform(1.5, 42.5); cy = rng.uniform(1.5, 42.5)
            if any(abs(cx-ox)+abs(cy-oy) < 2.2 for (ox,oy,_t) in centers): continue
            neg.append((crop(img, cal, cx, cy), 0))
        return pos, neg
    class Net(nn.Module):
        def __init__(self):
            super().__init__()
            def blk(i,o): return nn.Sequential(nn.Conv2d(i,o,3,padding=1), nn.BatchNorm2d(o), nn.ReLU(True), nn.MaxPool2d(2))
            self.f = nn.Sequential(blk(3,32), blk(32,64), blk(64,128), blk(128,192), nn.AdaptiveAvgPool2d(1))
            self.drop = nn.Dropout(0.25); self.head = nn.Linear(192, 2)
        def forward(self, x): return self.head(self.drop(self.f(x).flatten(1)))
    def batch(items):
        xs = np.stack([c[:, :, ::-1] for c, _ in items]).copy()
        x = torch.from_numpy(xs).permute(0,3,1,2).float().div(255).to(DEV)
        y = torch.tensor([l for _, l in items], dtype=torch.long).to(DEV)
        return x, y
    reports = []
    for hold in range(len(data)):
        tr = [b for i,b in enumerate(data) if i != hold]; va = data[hold]
        pos_tr, neg_tr = [], []
        for b in tr:
            p, n = samples(b); pos_tr += p; neg_tr += n
        net = Net().to(DEV)
        opt = torch.optim.AdamW(net.parameters(), lr=2e-3, weight_decay=2e-4)
        lossf = nn.CrossEntropyLoss(weight=torch.tensor([1.0, 3.0], device=DEV), label_smoothing=0.03)
        for ep in range(a.epochs):
            net.train(); rng.shuffle(pos_tr); rng.shuffle(neg_tr)
            for it in range(max(1,(len(pos_tr)+len(neg_tr))//64)):
                items = [pos_tr[rng.randrange(len(pos_tr))] for _ in range(40)] + [neg_tr[rng.randrange(len(neg_tr))] for _ in range(40)]
                items = [(aug(c,rng), l) for (c,l) in items]
                x, y = batch(items); loss = lossf(net(x), y); opt.zero_grad(); loss.backward(); opt.step()
        # 评估
        net.eval(); img, cal, centers = va["img"], va["cal"], va["centers"]
        gt = [(cx, cy, t) for (cx, cy, t) in centers]
        cells = [(cx, cy) for cx in range(2,42) for cy in range(2,42)]
        cand = []
        with torch.no_grad():
            for i in range(0, len(cells), 128):
                cs = cells[i:i+128]
                items = [(crop(img, cal, cx+.5, cy+.5), 0) for (cx,cy) in cs]
                x, _ = batch(items)
                prob = torch.softmax(net(x), 1)[:,1]
                for k,(cx,cy) in enumerate(cs):
                    cand.append((float(prob[k]), cx+.5, cy+.5))
        best = None
        for th in (0.5,0.6,0.7,0.8,0.9,0.95,0.98):
            sel = sorted([c for c in cand if c[0] >= th], reverse=True)
            kept = []
            for c in sel:
                if all(abs(c[1]-q[1]) + abs(c[2]-q[2]) > 1.9 for q in kept): kept.append(c)
            matched = set(); tp = 0
            for (s, cx, cy) in kept:
                bb = None
                for gi,(gx,gy,_t) in enumerate(gt):
                    if gi in matched: continue
                    d = abs(cx-gx) + abs(cy-gy)
                    if d < 1.6 and (bb is None or d < bb[0]): bb = (d, gi)
                if bb: matched.add(bb[1]); tp += 1
            prec = tp/max(1,len(kept)); rec = tp/max(1,len(gt)); f1 = 2*prec*rec/max(1e-9,prec+rec)
            if best is None or f1 > best[0]: best = (f1, th, prec, rec, tp, len(kept))
        f1, th, prec, rec, tp, npred = best
        print("hold base %d: gt=%d pred=%d tp=%d prec=%.3f recall=%.3f f1=%.3f @th=%.2f" % (va["bi"], len(gt), npred, tp, prec, rec, f1, th), flush=True)
        reports.append({"base": va["bi"], "gt": len(gt), "pred": npred, "tp": tp, "prec": prec, "recall": rec, "f1": f1, "th": th})
    mean = lambda k: sum(r[k] for r in reports)/len(reports)
    print("MEAN prec=%.3f recall=%.3f f1=%.3f" % (mean("prec"), mean("recall"), mean("f1")))
    json.dump({"reports": reports, "mean": {"prec": mean("prec"), "recall": mean("recall"), "f1": mean("f1")}},
              open(a.report, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("report", a.report)
if __name__ == "__main__":
    main()
