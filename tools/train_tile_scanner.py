# -*- coding: utf-8 -*-
"""全图逐格扫描器：每格判断 背景/38类建筑，留一基验证位置召回与类型准确率。

用法: python tools/train_tile_scanner.py --export a.json,b.json --epochs 30
"""
import argparse, json, os, random, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import cv2, numpy as np, torch, torch.nn as nn
from tools.apk_export_to_dataset import load_export
from clashlab.geo import Calib
S = 96
def build_base(path):
    d = json.load(open(path, encoding="utf-8"))
    img = cv2.imdecode(np.fromfile(os.path.join(BASE, "android", "assets", d["image"]), np.uint8), cv2.IMREAD_COLOR)
    wn, hn = d["image_size"]
    quad = np.float32([[u*wn, v*hn] for u, v in d["corners_norm"]])
    cal = Calib.from_quad(quad, n=44)
    blds = []
    for b in d["buildings"]:
        t = b["type"]; x, y = b["tile"]
        blds.append((t, x + 0.5, y + 0.5, x, y))
    return img, cal, blds, d
def crop_at(img, cal, tx, ty):
    x0, y0 = tx - 1.5, ty - 1.5
    p = [cal.tile_to_px(x0, y0), cal.tile_to_px(x0+4, y0), cal.tile_to_px(x0+4, y0+4), cal.tile_to_px(x0, y0+4)]
    H = cv2.getPerspectiveTransform(np.float32(p), np.float32([[0,0],[S,0],[S,S],[0,S]]))
    return cv2.warpPerspective(img, H, (S, S), flags=cv2.INTER_AREA)
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", required=True)
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--exclude", default="")
    ap.add_argument("--out", default=os.path.join(BASE, "models", "tile_scanner.pt"))
    ap.add_argument("--report", default=os.path.join(BASE, "out", "tile_scanner_report.json"))
    a = ap.parse_args()
    excl = {int(x) for x in a.exclude.split(",") if x.strip()}
    paths = [p.strip() for p in a.export.split(",") if p.strip() and os.path.exists(p.strip())]
    data = []
    for bi, p in enumerate(paths):
        if bi in excl: print("skip base", bi, flush=True); continue
        img, cal, blds, d = build_base(p)
        data.append({"bi": bi, "img": img, "cal": cal, "blds": blds, "path": p})
        print("load base", bi, "bld", len(blds), flush=True)
    types = sorted({t for b in data for (t, *_rest) in b["blds"]})
    TIDX = {t: i for i, t in enumerate(types)}; BG = len(types); NC = len(types) + 1
    print("bases", len(data), "types", len(types), flush=True)
    rng = random.Random(7); DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("device", DEV, flush=True)
    def samples_from(b, augment=False):
        img, cal, blds = b["img"], b["cal"], b["blds"]
        pos = {}; occ = []
        for (t, tx, ty, gx, gy) in blds:
            pos[(int(round(tx)), int(round(ty)))] = t; occ.append((tx, ty))
        xs = []
        for (cx, cy) in pos:
            c = crop_at(img, cal, cx + 0.5, cy + 0.5)
            if augment: c = aug(c, rng)
            xs.append((c, TIDX[pos[(cx, cy)]]))
        negs = []
        tries = 0
        while len(negs) < 90 and tries < 4000:
            tries += 1
            cx = rng.randint(2, 42); cy = rng.randint(2, 42)
            if any(abs(cx + .5 - ox) + abs(cy + .5 - oy) < 2.2 for ox, oy in occ): continue
            c = crop_at(img, cal, cx + .5, cy + .5)
            if augment: c = aug(c, rng)
            negs.append((c, BG))
        return xs, negs
    def aug(c, r):
        x = c.astype(np.float32) * r.uniform(0.85, 1.15) + r.uniform(-12, 12)
        x = np.clip(x, 0, 255)
        ang = r.uniform(-4, 4); sc = r.uniform(0.92, 1.08)
        M = cv2.getRotationMatrix2D((S/2, S/2), ang, sc)
        M[0,2] += r.uniform(-3,3); M[1,2] += r.uniform(-3,3)
        x = cv2.warpAffine(x, M, (S, S), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        return x.astype(np.uint8)
    class Net(nn.Module):
        def __init__(self, n):
            super().__init__()
            def blk(i,o): return nn.Sequential(nn.Conv2d(i,o,3,padding=1), nn.BatchNorm2d(o), nn.ReLU(True), nn.MaxPool2d(2))
            self.f = nn.Sequential(blk(3,32), blk(32,64), blk(64,128), blk(128,192), nn.AdaptiveAvgPool2d(1))
            self.drop = nn.Dropout(0.25); self.head = nn.Linear(192, n)
        def forward(self, x): return self.head(self.drop(self.f(x).flatten(1)))
    def batch(items, train):
        xs = np.stack([c[:, :, ::-1] for c, _ in items]).copy()
        x = torch.from_numpy(xs).permute(0,3,1,2).float().div(255).to(DEV)
        y = torch.tensor([l for _, l in items], dtype=torch.long).to(DEV)
        return x, y
    reports = []
    for hold in range(len(data)):
        tr = [b for i, b in enumerate(data) if i != hold]; va = data[hold]
        pos_tr, neg_tr = [], []
        for b in tr:
            p, n = samples_from(b, augment=True); pos_tr += p; neg_tr += n
        net = Net(NC).to(DEV)
        opt = torch.optim.AdamW(net.parameters(), lr=2e-3, weight_decay=2e-4)
        lossf = nn.CrossEntropyLoss(label_smoothing=0.05)
        steps = max(1, (len(pos_tr) + len(neg_tr)) // 64)
        for ep in range(a.epochs):
            net.train(); rng.shuffle(pos_tr); rng.shuffle(neg_tr)
            for it in range(steps):
                npos = 40; nneg = 24
                items = [pos_tr[rng.randrange(len(pos_tr))] for _ in range(npos)] + [neg_tr[rng.randrange(len(neg_tr))] for _ in range(nneg)]
                x, y = batch(items, True)
                loss = lossf(net(x), y); opt.zero_grad(); loss.backward(); opt.step()
        # 评估：全图扫描 + 阈值扫描 + 距离去重
        net.eval()
        img, cal, blds = va["img"], va["cal"], va["blds"]
        gt = [(t, tx, ty) for (t, tx, ty, gx, gy) in blds]
        cells = [(cx, cy) for cx in range(2, 42) for cy in range(2, 42)]
        cand = []
        with torch.no_grad():
            for i in range(0, len(cells), 128):
                cs = cells[i:i+128]
                items = [(crop_at(img, cal, cx + .5, cy + .5), 0) for (cx, cy) in cs]
                x, _ = batch(items, False)
                prob = torch.softmax(net(x), 1)
                for k, (cx, cy) in enumerate(cs):
                    score, cls = float(prob[k, :NC-1].max()), int(prob[k, :NC-1].argmax())
                    cand.append((score, cls, cx + .5, cy + .5))
        best_f1 = None; best_t = None
        for th in (0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
            sel = sorted([c for c in cand if c[0] >= th], reverse=True)
            kept = []
            for c in sel:
                if all(abs(c[2]-q[2]) + abs(c[3]-q[3]) > 1.2 for q in kept): kept.append(c)
            matched = set(); tp = 0; type_ok = 0
            for p_ in kept:
                best = None
                for gi, (tt, tx, ty) in enumerate(gt):
                    if gi in matched: continue
                    d = abs(p_[2]-tx) + abs(p_[3]-ty)
                    if d < 1.6 and (best is None or d < best[0]): best = (d, gi)
                if best:
                    matched.add(best[1]); tp += 1
                    if types[p_[1]] == gt[best[1]][0]: type_ok += 1
            prec = tp / max(1, len(kept)); rec = tp / max(1, len(gt))
            f1 = 2*prec*rec / max(1e-9, prec+rec)
            if best_f1 is None or f1 > best_f1[0]:
                best_f1 = (f1, th, prec, rec, tp, len(kept), type_ok)
        f1, th, prec, rec, tp, npred, tok = best_f1
        tacc = tok / max(1, tp)
        print("hold base %d: gt=%d pred=%d tp=%d prec=%.3f recall=%.3f f1=%.3f type_acc=%.3f @th=%.2f" % (va["bi"], len(gt), npred, tp, prec, rec, f1, tacc, th), flush=True)
        reports.append({"base": va["bi"], "gt": len(gt), "pred": npred, "tp": tp, "prec": prec, "recall": rec, "f1": f1, "type_acc": tacc, "th": th})
    mean = lambda k: sum(r[k] for r in reports)/len(reports)
    print("MEAN prec=%.3f recall=%.3f f1=%.3f type_acc=%.3f" % (mean("prec"), mean("recall"), mean("f1"), mean("type_acc")))
    # 全量训练保存
    pos_all, neg_all = [], []
    for b in data:
        p, n = samples_from(b, augment=True); pos_all += p; neg_all += n
    net = Net(NC).to(DEV); opt = torch.optim.AdamW(net.parameters(), lr=2e-3, weight_decay=2e-4); lossf = nn.CrossEntropyLoss(label_smoothing=0.05)
    for ep in range(a.epochs):
        net.train(); rng.shuffle(pos_all); rng.shuffle(neg_all)
        for it in range(max(1, (len(pos_all)+len(neg_all))//64)):
            items = [pos_all[rng.randrange(len(pos_all))] for _ in range(40)] + [neg_all[rng.randrange(len(neg_all))] for _ in range(24)]
            x, y = batch(items, True); loss = lossf(net(x), y); opt.zero_grad(); loss.backward(); opt.step()
    torch.save({"model": net.state_dict(), "types": types, "bg": BG, "size": S}, a.out)
    json.dump({"reports": reports, "bases": len(data), "types": types}, open(a.report, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("saved", a.out, a.report)
if __name__ == "__main__":
    main()
