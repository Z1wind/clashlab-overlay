# -*- coding: utf-8 -*-
"""阈值网格 CV：为三种模式反推最优 (gate_th, emb_th)。"""
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
    wn, hn = d["image_size"]; q = np.float32([[u*wn, v*hn] for u, v in d["corners_norm"]])
    return img, Calib.from_quad(q, n=44), [(b["type"], b["tile"][0], b["tile"][1]) for b in d["buildings"]]
def warp(img, cal, cx, cy):
    x0, y0 = cx-1.5, cy-1.5
    p = [cal.tile_to_px(x0,y0), cal.tile_to_px(x0+4,y0), cal.tile_to_px(x0+4,y0+4), cal.tile_to_px(x0,y0+4)]
    H = cv2.getPerspectiveTransform(np.float32(p), np.float32([[0,0],[S,0],[S,S],[0,S]]))
    return cv2.warpPerspective(img, H, (S,S), flags=cv2.INTER_AREA)
def aug(c, r):
    x = c.astype(np.float32)*r.uniform(0.85,1.15)+r.uniform(-12,12); return np.clip(x,0,255).astype(np.uint8)
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
    oh = torch.zeros_like(cos); oh.scatter_(1, y.view(-1,1), 1)
    return torch.cos(th + m*oh) * s
def main():
    paths = [os.path.join(os.path.expanduser("~"), "Downloads", "annot_b01 (1).json"),
             os.path.join(os.path.expanduser("~"), "Downloads", "annot_b02 (1).json")]
    paths += [os.path.join(os.path.expanduser("~"), "Downloads", "annot_b%02d.json" % i) for i in range(3, 9)]
    data = []
    for p in paths:
        img, cal, blds = prep(p); data.append({"img": img, "cal": cal, "blds": blds})
    types = sorted({t for b in data for (t,_,_) in b["blds"]}); TIDX = {t:i for i,t in enumerate(types)}
    NC = len(types); BG = NC; NCLS = NC+1
    DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("types", NC, "device", DEV, flush=True)
    grid_g = [round(0.40+0.05*i,2) for i in range(12)]   # 0.40..0.95
    grid_e = [round(0.40+0.05*i,2) for i in range(12)]
    acc = {(g,e): {"prec":[], "recall":[], "type":[], "pred":[]} for g in grid_g for e in grid_e}
    for hold in range(len(data)):
        tr = [b for i,b in enumerate(data) if i != hold]; va = data[hold]
        rng = random.Random(7)
        gpos, gneg = [], []
        for b in tr:
            for (t, gx, gy) in b["blds"]: gpos.append((warp(b["img"], b["cal"], gx, gy), 1))
            tries = 0
            while tries < 12000 and len(gneg) < 110*len(tr):
                tries += 1
                cx = rng.uniform(1.5,42.5); cy = rng.uniform(1.5,42.5)
                if any(abs(cx-(gx+.5))+abs(cy-(gy+.5)) < 2.2 for (_,gx,gy) in b["blds"]): continue
                gneg.append((warp(b["img"], b["cal"], cx, cy), 0))
        gate = Net(2).to(DEV); opt = torch.optim.AdamW(gate.parameters(), lr=2e-3, weight_decay=2e-4)
        lossf = nn.CrossEntropyLoss(weight=torch.tensor([1.0,3.0], device=DEV), label_smoothing=0.03)
        for ep in range(24):
            gate.train(); rng.shuffle(gpos); rng.shuffle(gneg)
            for it in range(max(1,(len(gpos)+len(gneg))//80)):
                items = [gpos[rng.randrange(len(gpos))] for _ in range(40)] + [gneg[rng.randrange(len(gneg))] for _ in range(40)]
                xs = np.stack([c for c,_ in items])[:,:,:,::-1].copy()
                x = torch.from_numpy(xs).permute(0,3,1,2).float().div(255).to(DEV)
                y = torch.tensor([l for _,l in items], dtype=torch.long).to(DEV)
                loss = lossf(gate(x), y); opt.zero_grad(); loss.backward(); opt.step()
        crops, labels = [], []
        for b in tr:
            for (t, gx, gy) in b["blds"]:
                crops.append(warp(b["img"], b["cal"], gx, gy)); labels.append(TIDX[t])
        bg = []
        for b in tr:
            tries = 0
            while tries < 12000 and len(bg) < len(crops):
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
        emb.eval(); gate.eval(); protos, proto_cls = [], []
        with torch.no_grad():
            for cls in range(NCLS):
                sel = [i for i,l in enumerate(labels_all) if l == cls][:12 if cls == BG else 6]
                if not sel: continue
                xs = np.stack([crops_all[i] for i in sel])[:,:,:,::-1].copy()
                x = torch.from_numpy(xs).permute(0,3,1,2).float().div(255).to(DEV)
                for v in emb(x).cpu().numpy(): protos.append(v); proto_cls.append(cls)
        P = np.stack(protos); PC = np.array(proto_cls)
        img, cal, blds = va["img"], va["cal"], va["blds"]
        gt = [(t, gx+.5, gy+.5) for (t,gx,gy) in blds]
        cells = [(cx, cy) for cx in range(2,42) for cy in range(2,42)]
        feats = []
        with torch.no_grad():
            for i in range(0, len(cells), 128):
                cs = cells[i:i+128]
                xs = np.stack([warp(img, cal, cx, cy) for (cx,cy) in cs])[:,:,:,::-1].copy()
                x = torch.from_numpy(xs).permute(0,3,1,2).float().div(255).to(DEV)
                gp = torch.softmax(gate(x), 1)[:,1].cpu().numpy()
                e = emb(x).cpu().numpy()
                sim = e @ P.T
                bmap = np.flatnonzero(PC != BG); bgmap = np.flatnonzero(PC == BG)
                best_b = sim[:, bmap].max(1); best_bi = sim[:, bmap].argmax(1); best_bg = sim[:, bgmap].max(1)
                for k, cell in enumerate(cs):
                    feats.append((cell[0]+.5, cell[1]+.5, float(gp[k]), float(best_b[k]), float(best_bg[k]),
                                  types[int(PC[bmap[best_bi[k]]])]))
        for g in grid_g:
            for e in grid_e:
                kept = []
                for (cx, cy, gp, bs, bgm, tname) in sorted([f for f in feats if f[2] >= g and f[3] >= e and f[3] > f[4]], key=lambda z: -z[3]):
                    if all(abs(cx-q[0]) + abs(cy-q[1]) > 1.9 for q in kept): kept.append((cx, cy, bs, bgm, tname))
                matched = set(); tp = tok = 0
                for (cx, cy, bs, bgm, tname) in kept:
                    bb = None
                    for gi,(tt,gx,gy) in enumerate(gt):
                        if gi in matched: continue
                        dd = abs(cx-gx)+abs(cy-gy)
                        if dd < 1.6 and (bb is None or dd < bb[0]): bb = (dd, gi)
                    if bb:
                        matched.add(bb[1]); tp += 1
                        if tname == gt[bb[1]][0]: tok += 1
                rec = {"prec": tp/max(1,len(kept)), "recall": tp/max(1,len(gt)), "type": tok/max(1,tp), "pred": len(kept)}
                for k,v in rec.items(): acc[(g,e)][k].append(v)
        print("fold", hold, "done", flush=True)
    rows = []
    for (g,e), v in acc.items():
        rows.append({"g": g, "e": e, "prec": float(np.mean(v["prec"])), "recall": float(np.mean(v["recall"])),
                     "type": float(np.mean(v["type"])), "pred": float(np.mean(v["pred"]))})
    json.dump(rows, open(os.path.join(BASE,"out","mode_threshold_grid.json"), "w", encoding="utf-8"), indent=1)
    def best_f1(r): return 2*r["prec"]*r["recall"]/max(1e-9, r["prec"]+r["recall"])
    std = max(rows, key=best_f1)
    rec = max([r for r in rows if r["prec"] >= 0.75] or rows, key=lambda r: r["recall"])
    pre = max([r for r in rows if r["recall"] >= 0.65] or rows, key=lambda r: r["prec"])
    for name, r in (("standard", std), ("recall", rec), ("precise", pre)):
        print("MODE %-9s gate=%.2f emb=%.2f  prec=%.3f recall=%.3f f1=%.3f type=%.3f pred=%.0f" % (
            name, r["g"], r["e"], r["prec"], r["recall"], best_f1(r), r["type"], r["pred"]))
if __name__ == "__main__":
    main()
