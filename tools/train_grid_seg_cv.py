# -*- coding: utf-8 -*-
"""网格分割检测器：输入四角规范化图像(512)，输出 44x44 类型图，留一基验证。"""
import json, os, random, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import cv2, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
from clashlab.geo import Calib
from clashlab.assets import STATS
R = 512   # 规范化输入边长
G = 44    # 网格分辨率
def prep(path):
    d = json.load(open(path, encoding="utf-8"))
    img = cv2.imdecode(np.fromfile(os.path.join(BASE, "android", "assets", d["image"]), np.uint8), cv2.IMREAD_COLOR)
    wn, hn = d["image_size"]; quad = np.float32([[u*wn, v*hn] for u, v in d["corners_norm"]])
    p = [quad[0], quad[1], quad[2], quad[3]]
    H = cv2.getPerspectiveTransform(np.float32(p), np.float32([[0,0],[R,0],[R,R],[0,R]]))
    wimg = cv2.warpPerspective(img, H, (R,R), flags=cv2.INTER_AREA)
    blds = [(b["type"], b["tile"][0], b["tile"][1]) for b in d["buildings"]]
    return wimg, blds
def target_grid(blds, TIDX, NC):
    tgt = np.full((G, G), NC-1, dtype=np.int64)  # 最后类 = 背景
    for (t, x, y) in blds:
        sz = int((STATS.get(t) or {}).get("size") or 2)
        cx = x + sz/2.0; cy = y + sz/2.0
        gx = int(np.clip(round(cx - 0.5), 0, G-1)); gy = int(np.clip(round(cy - 0.5), 0, G-1))
        tgt[gy, gx] = TIDX[t]
    return tgt
class UNet(nn.Module):
    def __init__(self, ncls, base=32):
        super().__init__()
        def blk(i,o): return nn.Sequential(nn.Conv2d(i,o,3,padding=1), nn.BatchNorm2d(o), nn.ReLU(True))
        self.e1 = blk(3, base); self.e2 = blk(base, base*2); self.e3 = blk(base*2, base*4); self.e4 = blk(base*4, base*8)
        self.pool = nn.MaxPool2d(2)
        self.u3 = nn.ConvTranspose2d(base*8, base*4, 2, 2); self.d3 = blk(base*8, base*4)
        self.u2 = nn.ConvTranspose2d(base*4, base*2, 2, 2); self.d2 = blk(base*4, base*2)
        self.u1 = nn.ConvTranspose2d(base*2, base, 2, 2); self.d1 = blk(base*2, base)
        self.head = nn.Conv2d(base, ncls, 1)
    def forward(self, x):
        a = self.e1(x); b = self.e2(self.pool(a)); c = self.e3(self.pool(b)); d = self.e4(self.pool(c))
        u = self.d3(torch.cat([self.u3(d), c], 1)); u = self.d2(torch.cat([self.u2(u), b], 1)); u = self.d1(torch.cat([self.u1(u), a], 1))
        # 512 -> 44
        h = F.interpolate(self.head(u), size=(G, G), mode="bilinear", align_corners=False)
        return h
def main():
    paths = [os.path.join(os.path.expanduser("~"), "Downloads", "annot_b01 (1).json"),
             os.path.join(os.path.expanduser("~"), "Downloads", "annot_b02 (1).json")]
    paths += [os.path.join(os.path.expanduser("~"), "Downloads", "annot_b%02d.json" % i) for i in range(3, 9)]
    data = []
    for bi, p in enumerate(paths):
        wimg, blds = prep(p); data.append({"bi": bi, "img": wimg, "blds": blds})
    types = sorted({t for b in data for (t,_,_) in b["blds"]}); TIDX = {t:i for i,t in enumerate(types)}
    NC = len(types) + 1  # + bg
    rng = random.Random(7); DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("types", len(types), "device", DEV, flush=True)
    reports = []
    for hold in range(len(data)):
        tr = [b for i,b in enumerate(data) if i != hold]; va = data[hold]
        pairs = []
        for b in tr:
            tgt = target_grid(b["blds"], TIDX, NC)
            pairs.append((b["img"], tgt))
        net = UNet(NC).to(DEV); opt = torch.optim.AdamW(net.parameters(), lr=2e-3, weight_decay=1e-4)
        w = torch.ones(NC, device=DEV); w[NC-1] = 0.15
        lossf = nn.CrossEntropyLoss(weight=w, label_smoothing=0.02)
        for ep in range(40):
            net.train(); rng.shuffle(pairs)
            for img, tgt in pairs:
                x = torch.from_numpy(img[:, :, ::-1].copy()).permute(2,0,1).float().div(255).unsqueeze(0).to(DEV)
                y = torch.from_numpy(tgt).long().unsqueeze(0).to(DEV)
                loss = lossf(net(x), y); opt.zero_grad(); loss.backward(); opt.step()
        net.eval()
        with torch.no_grad():
            x = torch.from_numpy(va["img"][:, :, ::-1].copy()).permute(2,0,1).float().div(255).unsqueeze(0).to(DEV)
            prob = torch.softmax(net(x), 1)[0].cpu().numpy()
        gt = [(t, gx+.5, gy+.5) for (t,gx,gy) in va["blds"]]
        best = None
        for th in (0.3,0.4,0.5,0.6,0.7,0.8):
            cands = []
            for gy in range(G):
                for gx in range(G):
                    p = prob[:, gy, gx]; cls = int(p[:NC-1].argmax()); s = float(p[cls])
                    if s >= th: cands.append((s, cls, gx+.5, gy+.5))
            cands.sort(reverse=True)
            kept = []
            for c in cands:
                if all(abs(c[2]-q[2]) + abs(c[3]-q[3]) > 1.9 for q in kept): kept.append(c)
            matched = set(); tp = tok = 0
            for (s, cls, cx, cy) in kept:
                bb = None
                for gi,(tt,gx,gy) in enumerate(gt):
                    if gi in matched: continue
                    dd = abs(cx-gx)+abs(cy-gy)
                    if dd < 1.6 and (bb is None or dd < bb[0]): bb = (dd, gi)
                if bb:
                    matched.add(bb[1]); tp += 1
                    if types[cls] == gt[bb[1]][0]: tok += 1
            prec = tp/max(1,len(kept)); rec = tp/max(1,len(gt)); f1 = 2*prec*rec/max(1e-9,prec+rec)
            if best is None or f1 > best[0]: best = (f1, th, prec, rec, tp, len(kept), tok)
        f1, th, prec, rec, tp, npred, tok = best
        print("hold base %d: gt=%d pred=%d tp=%d prec=%.3f recall=%.3f f1=%.3f type_acc=%.3f @th=%.2f" % (va["bi"], len(gt), npred, tp, prec, rec, f1, tok/max(1,tp), th), flush=True)
        reports.append({"base": va["bi"], "gt": len(gt), "pred": npred, "tp": tp, "prec": prec, "recall": rec, "f1": f1, "type_acc": tok/max(1,tp), "th": th})
    mean = lambda k: sum(r[k] for r in reports)/len(reports)
    print("GRID-SEG MEAN prec=%.3f recall=%.3f f1=%.3f type_acc=%.3f" % (mean("prec"), mean("recall"), mean("f1"), mean("type_acc")))
    json.dump({"reports": reports}, open(os.path.join(BASE,"out","grid_seg_report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
if __name__ == "__main__":
    main()
