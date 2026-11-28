# -*- coding: utf-8 -*-
"""方案2 混合：CNN 门控出候选 + embedding 最近邻认类型/校验（留一基）。"""
import json, os, random, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import cv2, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
from clashlab.geo import Calib
S = 96
def prep(path):
    d = json.load(open(path, encoding="utf-8"))
    img = cv2.imdecode(np.fromfile(os.path.join(BASE, "android", "assets", d["image"]), np.uint8), cv2.IMREAD_COLOR)
    wn, hn = d["image_size"]; quad = np.float32([[u*wn, v*hn] for u, v in d["corners_norm"]])
    return img, Calib.from_quad(quad, n=44), [(b["type"], b["tile"][0], b["tile"][1]) for b in d["buildings"]]
def warp(img, cal, cx, cy):
    x0, y0 = cx-1.5, cy-1.5
    p = [cal.tile_to_px(x0,y0), cal.tile_to_px(x0+4,y0), cal.tile_to_px(x0+4,y0+4), cal.tile_to_px(x0,y0+4)]
    H = cv2.getPerspectiveTransform(np.float32(p), np.float32([[0,0],[S,0],[S,S],[0,S]]))
    return cv2.warpPerspective(img, H, (S,S), flags=cv2.INTER_AREA)
def aug(c, r):
    x = c.astype(np.float32)*r.uniform(0.85,1.15)+r.uniform(-12,12); x=np.clip(x,0,255)
    M = cv2.getRotationMatrix2D((S/2,S/2), r.uniform(-4,4), r.uniform(0.92,1.08))
    M[0,2]+=r.uniform(-3,3); M[1,2]+=r.uniform(-3,3)
    x = cv2.warpAffine(x, M, (S,S), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return x.astype(np.uint8)
class Net(nn.Module):
    def __init__(self, n):
        super().__init__()
        def blk(i,o): return nn.Sequential(nn.Conv2d(i,o,3,padding=1), nn.BatchNorm2d(o), nn.ReLU(True), nn.MaxPool2d(2))
        self.f = nn.Sequential(blk(3,32), blk(32,64), blk(64,128), blk(128,192), nn.AdaptiveAvgPool2d(1))
        self.drop = nn.Dropout(0.2); self.head = nn.Linear(192, n)
    def forward(self, x): return self.head(self.drop(self.f(x).flatten(1)))
class Emb(nn.Module):
    def __init__(self, n, dim=128):
        super().__init__()
        def blk(i,o): return nn.Sequential(nn.Conv2d(i,o,3,padding=1), nn.BatchNorm2d(o), nn.ReLU(True), nn.MaxPool2d(2))
        self.f = nn.Sequential(blk(3,32), blk(32,64), blk(64,128), blk(128,192), nn.AdaptiveAvgPool2d(1))
        self.drop = nn.Dropout(0.2); self.proj = nn.Linear(192, dim); self.weight = nn.Parameter(torch.randn(n, dim))
    def forward(self, x): return F.normalize(self.proj(self.drop(self.f(x).flatten(1))), dim=1)
def arcface(e, w, y, s=16.0, m=0.25):
    cos = e @ F.normalize(w, dim=1).t(); th = torch.acos(torch.clamp(cos, -0.999, 0.999))
    onehot = torch.zeros_like(cos); onehot.scatter_(1, y.view(-1,1), 1)
    return torch.cos(th + m*onehot) * s
def main():
    paths = [os.path.join(os.path.expanduser("~"), "Downloads", "annot_b01 (1).json"),
             os.path.join(os.path.expanduser("~"), "Downloads", "annot_b02 (1).json")]
    paths += [os.path.join(os.path.expanduser("~"), "Downloads", "annot_b%02d.json" % i) for i in range(3, 9)]
    data = []
    for bi, p in enumerate(paths):
        img, cal, blds = prep(p); data.append({"bi": bi, "img": img, "cal": cal, "blds": blds})
    types = sorted({t for b in data for (t,_,_) in b["blds"]}); TIDX = {t:i for i,t in enumerate(types)}
    NC = len(types); BG = NC; NCLS = NC+1
    rng = random.Random(7); DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("types", NC, "device", DEV, flush=True)
    reports = []
    for hold in range(len(data)):
        tr = [b for i,b in enumerate(data) if i != hold]; va = data[hold]
        # ---- 门控 ----
        gpos, gneg, gpos_types = [], [], []
        for b in tr:
            for (t, gx, gy) in b["blds"]:
                gpos.append((warp(b["img"], b["cal"], gx, gy), 1)); gpos_types.append(t)
            tries = 0
            while tries < 8000 and len(gneg) < 110*len(tr):
                tries += 1
                cx = rng.uniform(1.5,42.5); cy = rng.uniform(1.5,42.5)
                if any(abs(cx-(gx+.5))+abs(cy-(gy+.5)) < 2.2 for (_,gx,gy) in b["blds"]): continue
                gneg.append((warp(b["img"], b["cal"], cx, cy), 0))
        gate = Net(2).to(DEV); opt = torch.optim.AdamW(gate.parameters(), lr=2e-3, weight_decay=2e-4)
        lossf = nn.CrossEntropyLoss(weight=torch.tensor([1.0,3.0], device=DEV), label_smoothing=0.03)
        for ep in range(26):
            gate.train(); rng.shuffle(gpos); rng.shuffle(gneg)
            for it in range(max(1,(len(gpos)+len(gneg))//80)):
                _cnt = {}
                for _t in gpos_types: _cnt[_t] = _cnt.get(_t, 0) + 1
                _w = [1.0 / (_cnt[_t] ** 0.5) for _t in gpos_types]
                _pick = rng.choices(gpos, weights=_w, k=40)
                items = [(aug(c,rng),l) for (c,l) in _pick + [gneg[rng.randrange(len(gneg))] for _ in range(40)]]
                xs = np.stack([c for c,_ in items])[:,:,:,::-1].copy()
                x = torch.from_numpy(xs).permute(0,3,1,2).float().div(255).to(DEV)
                y = torch.tensor([l for _,l in items], dtype=torch.long).to(DEV)
                loss = lossf(gate(x), y); opt.zero_grad(); loss.backward(); opt.step()
        # ---- embedding ----
        crops, labels = [], []
        for b in tr:
            for (t, gx, gy) in b["blds"]:
                crops.append(warp(b["img"], b["cal"], gx, gy)); labels.append(TIDX[t])
        bg = []
        for b in tr:
            tries = 0
            while tries < 4000 and len(bg) < len(crops):
                tries += 1
                cx = rng.uniform(1.5,42.5); cy = rng.uniform(1.5,42.5)
                if any(abs(cx-(gx+.5))+abs(cy-(gy+.5)) < 2.2 for (_,gx,gy) in b["blds"]): continue
                bg.append(warp(b["img"], b["cal"], cx, cy))
        crops_all = crops + bg; labels_all = labels + [BG]*len(bg)
        emb = Emb(NCLS).to(DEV); opt2 = torch.optim.AdamW(emb.parameters(), lr=2e-3, weight_decay=2e-4)
        lossf_emb = nn.CrossEntropyLoss(label_smoothing=0.05)
        for ep in range(30):
            emb.train(); idx = list(range(len(crops_all))); rng.shuffle(idx)
            for it in range(max(1, len(idx)//64)):
                sel = idx[it*64:(it+1)*64]
                xs = np.stack([aug(crops_all[i], rng) for i in sel])[:,:,:,::-1].copy()
                x = torch.from_numpy(xs).permute(0,3,1,2).float().div(255).to(DEV)
                y = torch.tensor([labels_all[i] for i in sel], dtype=torch.long).to(DEV)
                loss = lossf_emb(arcface(emb(x), emb.weight, y), y); opt2.zero_grad(); loss.backward(); opt2.step()
        # ---- 原型 ----
        emb.eval(); gate.eval(); protos, proto_cls = [], []
        with torch.no_grad():
            for cls in range(NCLS):
                sel = [i for i,l in enumerate(labels_all) if l == cls][:12 if cls == BG else 6]
                if not sel: continue
                xs = np.stack([crops_all[i] for i in sel])[:,:,:,::-1].copy()
                x = torch.from_numpy(xs).permute(0,3,1,2).float().div(255).to(DEV)
                for v in emb(x).cpu().numpy(): protos.append(v); proto_cls.append(cls)
        P = np.stack(protos); PC = np.array(proto_cls)
        # ---- 评估 ----
        img, cal, blds = va["img"], va["cal"], va["blds"]
        gt = [(t, gx+.5, gy+.5) for (t,gx,gy) in blds]
        cells = [(cx, cy) for cx in range(2,42) for cy in range(2,42)]
        gate_prob, embs = {}, {}
        with torch.no_grad():
            for i in range(0, len(cells), 128):
                cs = cells[i:i+128]
                xs = np.stack([warp(img, cal, cx, cy) for (cx,cy) in cs])[:,:,:,::-1].copy()
                x = torch.from_numpy(xs).permute(0,3,1,2).float().div(255).to(DEV)
                gp = torch.softmax(gate(x), 1)[:,1].cpu().numpy()
                e = emb(x).cpu().numpy()
                for k, cell in enumerate(cs):
                    gate_prob[cell] = float(gp[k]); embs[cell] = e[k]
        best = None
        for gth in (0.5,0.6,0.7,0.8,0.9):
            cand = []
            for cell in cells:
                if gate_prob[cell] < gth: continue
                e = embs[cell]; sim = P @ e
                bidx = int(sim.argmax()); cls = int(PC[bidx]); bs = float(sim[bidx])
                bgmax = float(sim[PC == BG].max()) if (PC == BG).any() else -1
                cand.append((bs, bs - bgmax, cls, cell[0]+.5, cell[1]+.5))
            cand.sort(reverse=True)
            for eth in (0.6,0.7,0.75,0.8,0.85,0.9):
                sel = [c for c in cand if c[0] >= eth and c[1] > 0]
                kept = []
                for c in sel:
                    if all(abs(c[3]-q[3]) + abs(c[4]-q[4]) > 1.9 for q in kept): kept.append(c)
                matched = set(); tp = tok = 0
                for (s, mg, cls, cx, cy) in kept:
                    bb = None
                    for gi,(tt,gx,gy) in enumerate(gt):
                        if gi in matched: continue
                        d = abs(cx-gx)+abs(cy-gy)
                        if d < 1.6 and (bb is None or d < bb[0]): bb = (d, gi)
                    if bb:
                        matched.add(bb[1]); tp += 1
                        if types[cls] == gt[bb[1]][0]: tok += 1
                prec = tp/max(1,len(kept)); rec = tp/max(1,len(gt)); f1 = 2*prec*rec/max(1e-9,prec+rec)
                if best is None or f1 > best[0]: best = (f1, gth, eth, prec, rec, tp, len(kept), tok)
        f1, gth, eth, prec, rec, tp, npred, tok = best
        print("hold base %d: gt=%d pred=%d tp=%d prec=%.3f recall=%.3f f1=%.3f type_acc=%.3f @gate=%.1f emb=%.2f" % (va["bi"], len(gt), npred, tp, prec, rec, f1, tok/max(1,tp), gth, eth), flush=True)
        reports.append({"base": va["bi"], "gt": len(gt), "pred": npred, "tp": tp, "prec": prec, "recall": rec, "f1": f1, "type_acc": tok/max(1,tp), "gth": gth, "eth": eth})
    mean = lambda k: sum(r[k] for r in reports)/len(reports)
    print("HYBRID MEAN prec=%.3f recall=%.3f f1=%.3f type_acc=%.3f" % (mean("prec"), mean("recall"), mean("f1"), mean("type_acc")))
    json.dump({"reports": reports}, open(os.path.join(BASE,"out","hybrid_balgate_report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
if __name__ == "__main__":
    main()
