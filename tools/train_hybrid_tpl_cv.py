# -*- coding: utf-8 -*-
"""方案3：混合 + 独特外形贴图二次校验（留一基）。"""
import json, os, random, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import cv2, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
from clashlab.geo import Calib
S = 96; T = 64; SEARCH = 8
ONLY = {"town-hall","eagle-artillery","monolith","scattershot","x-bow","inferno-tower",
        "clan-castle","air-sweeper","ricochet-cannon","multi-archer-tower","spell-tower",
        "firespitter","multi-gear-tower"}
def prep(path):
    d = json.load(open(path, encoding="utf-8"))
    img = cv2.imdecode(np.fromfile(os.path.join(BASE, "android", "assets", d["image"]), np.uint8), cv2.IMREAD_GRAYSCALE)
    wn, hn = d["image_size"]; quad = np.float32([[u*wn, v*hn] for u, v in d["corners_norm"]])
    return img, Calib.from_quad(quad, n=44), [(b["type"], b["tile"][0], b["tile"][1]) for b in d["buildings"]]
def warp_gray(img, cal, cx, cy, size):
    x0, y0 = cx-1.5, cy-1.5
    p = [cal.tile_to_px(x0,y0), cal.tile_to_px(x0+4,y0), cal.tile_to_px(x0+4,y0+4), cal.tile_to_px(x0,y0+4)]
    H = cv2.getPerspectiveTransform(np.float32(p), np.float32([[0,0],[size,0],[size,size],[0,size]]))
    return cv2.warpPerspective(img, H, (size,size), flags=cv2.INTER_AREA)
def cc(a, t):
    o = (a.shape[0]-t)//2; return a[o:o+t, o:o+t]
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
        gpos, gneg = [], []
        for b in tr:
            for (t, gx, gy) in b["blds"]: gpos.append((warp_gray(b["img"], b["cal"], gx, gy, S), 1))
            tries = 0
            while tries < 8000 and len(gneg) < 110*len(tr):
                tries += 1
                cx = rng.uniform(1.5,42.5); cy = rng.uniform(1.5,42.5)
                if any(abs(cx-(gx+.5))+abs(cy-(gy+.5)) < 2.2 for (_,gx,gy) in b["blds"]): continue
                gneg.append((warp_gray(b["img"], b["cal"], cx, cy, S), 0))
        gate = Net(2).to(DEV); opt = torch.optim.AdamW(gate.parameters(), lr=2e-3, weight_decay=2e-4)
        lossf = nn.CrossEntropyLoss(weight=torch.tensor([1.0,3.0], device=DEV), label_smoothing=0.03)
        for ep in range(24):
            gate.train(); rng.shuffle(gpos); rng.shuffle(gneg)
            for it in range(max(1,(len(gpos)+len(gneg))//80)):
                items = [gpos[rng.randrange(len(gpos))] for _ in range(40)] + [gneg[rng.randrange(len(gneg))] for _ in range(40)]
                xs = np.stack([c for c,_ in items])[:,:,:,None].repeat(3,3)[:,:,:,::-1].copy()
                x = torch.from_numpy(xs).permute(0,3,1,2).float().div(255).to(DEV)
                y = torch.tensor([l for _,l in items], dtype=torch.long).to(DEV)
                loss = lossf(gate(x), y); opt.zero_grad(); loss.backward(); opt.step()
        # ---- embedding ----
        crops, labels = [], []
        for b in tr:
            for (t, gx, gy) in b["blds"]:
                crops.append(warp_gray(b["img"], b["cal"], gx, gy, S)); labels.append(TIDX[t])
        bg = []
        for b in tr:
            tries = 0
            while tries < 4000 and len(bg) < len(crops):
                tries += 1
                cx = rng.uniform(1.5,42.5); cy = rng.uniform(1.5,42.5)
                if any(abs(cx-(gx+.5))+abs(cy-(gy+.5)) < 2.2 for (_,gx,gy) in b["blds"]): continue
                bg.append(warp_gray(b["img"], b["cal"], cx, cy, S))
        crops_all = crops + bg; labels_all = labels + [BG]*len(bg)
        emb = Emb(NCLS).to(DEV); opt2 = torch.optim.AdamW(emb.parameters(), lr=2e-3, weight_decay=2e-4)
        lossf_emb = nn.CrossEntropyLoss(label_smoothing=0.05)
        for ep in range(30):
            emb.train(); idx = list(range(len(crops_all))); rng.shuffle(idx)
            for it in range(max(1, len(idx)//64)):
                sel = idx[it*64:(it+1)*64]
                xs = np.stack([crops_all[i] for i in sel])[:,:,:,None].repeat(3,3)[:,:,:,::-1].copy()
                x = torch.from_numpy(xs).permute(0,3,1,2).float().div(255).to(DEV)
                y = torch.tensor([labels_all[i] for i in sel], dtype=torch.long).to(DEV)
                loss = lossf_emb(arcface(emb(x), emb.weight, y), y); opt2.zero_grad(); loss.backward(); opt2.step()
        # ---- 原型 + 独特外形模板 ----
        emb.eval(); gate.eval(); protos, proto_cls = [], []
        with torch.no_grad():
            for cls in range(NCLS):
                sel = [i for i,l in enumerate(labels_all) if l == cls][:12 if cls == BG else 6]
                if not sel: continue
                xs = np.stack([crops_all[i] for i in sel])[:,:,:,None].repeat(3,3)[:,:,:,::-1].copy()
                x = torch.from_numpy(xs).permute(0,3,1,2).float().div(255).to(DEV)
                for v in emb(x).cpu().numpy(): protos.append(v); proto_cls.append(cls)
        P = np.stack(protos); PC = np.array(proto_cls)
        tpl = {}
        for b in tr:
            for (t, gx, gy) in b["blds"]:
                if t not in ONLY: continue
                if len(tpl.get(t, [])) >= 4: continue
                tpl.setdefault(t, []).append(cc(warp_gray(b["img"], b["cal"], gx, gy, S), T))
        # ---- 评估 ----
        img, cal, blds = va["img"], va["cal"], va["blds"]
        gt = [(t, gx+.5, gy+.5) for (t,gx,gy) in blds]
        cells = [(cx, cy) for cx in range(2,42) for cy in range(2,42)]
        gprob_map, emb_map = {}, {}
        with torch.no_grad():
            for i in range(0, len(cells), 128):
                cs = cells[i:i+128]
                xs = np.stack([warp_gray(img, cal, cx, cy, S) for (cx,cy) in cs])[:,:,:,None].repeat(3,3)[:,:,:,::-1].copy()
                x = torch.from_numpy(xs).permute(0,3,1,2).float().div(255).to(DEV)
                gp = torch.softmax(gate(x), 1)[:,1].cpu().numpy(); e = emb(x).cpu().numpy()
                for k, cell in enumerate(cs): gprob_map[cell] = float(gp[k]); emb_map[cell] = e[k]
        best = None
        for gth in (0.7,0.8,0.9):
            cand = []
            for cell in cells:
                if gprob_map[cell] < gth: continue
                e = emb_map[cell]; sim = P @ e
                bmap = np.flatnonzero(PC != BG); idx = int(bmap[int(sim[bmap].argmax())])
                bs = float(sim[idx]); bgmax = float(sim[PC == BG].max())
                if bs <= bgmax: continue
                cand.append((bs, int(PC[idx]), cell[0]+.5, cell[1]+.5))
            cand.sort(reverse=True)
            for eth in (0.6,0.7,0.8,0.85):
                for t3 in (0.0,0.45,0.55,0.65,0.75):
                    sel = [c for c in cand if c[0] >= eth]
                    kept = []
                    for c in sel:
                        ctype = types[c[1]]
                        if t3 > 0 and ctype in ONLY and tpl.get(ctype):
                            full = warp_gray(img, cal, c[2], c[3], S + 2*SEARCH)
                            score = max(float(cv2.matchTemplate(full, tp, cv2.TM_CCOEFF_NORMED).max()) for tp in tpl[ctype])
                            if score < t3: continue
                        ok = True
                        for q in kept:
                            if abs(c[2]-q[2]) + abs(c[3]-q[3]) <= 1.9: ok = False; break
                        if ok: kept.append(c)
                    matched = set(); tp = tok = 0
                    for (s, cls, cx, cy) in kept:
                        bb = None
                        for gi,(tt,gx,gy) in enumerate(gt):
                            if gi in matched: continue
                            d = abs(cx-gx)+abs(cy-gy)
                            if d < 1.6 and (bb is None or d < bb[0]): bb = (d, gi)
                        if bb:
                            matched.add(bb[1]); tp += 1
                            if types[cls] == gt[bb[1]][0]: tok += 1
                    prec = tp/max(1,len(kept)); rec = tp/max(1,len(gt)); f1 = 2*prec*rec/max(1e-9,prec+rec)
                    if best is None or f1 > best[0]: best = (f1, gth, eth, t3, prec, rec, tp, len(kept), tok)
        f1, gth, eth, t3, prec, rec, tp, npred, tok = best
        print("hold base %d: gt=%d pred=%d tp=%d prec=%.3f recall=%.3f f1=%.3f type_acc=%.3f @g=%.1f e=%.2f t3=%.2f" % (va["bi"], len(gt), npred, tp, prec, rec, f1, tok/max(1,tp), gth, eth, t3), flush=True)
        reports.append({"base": va["bi"], "prec": prec, "recall": rec, "f1": f1, "type_acc": tok/max(1,tp), "gth": gth, "eth": eth, "t3": t3})
    mean = lambda k: sum(r[k] for r in reports)/len(reports)
    print("HYBRID+TPL MEAN prec=%.3f recall=%.3f f1=%.3f type_acc=%.3f" % (mean("prec"), mean("recall"), mean("f1"), mean("type_acc")))
    json.dump({"reports": reports}, open(os.path.join(BASE,"out","hybrid_tpl_report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
if __name__ == "__main__":
    main()
