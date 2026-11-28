# -*- coding: utf-8 -*-
"""真实 8 张标注：增强版训练（112px + 颜色/几何增强 + 类平衡 + 分类型指标）。"""
import argparse, json, os, random, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import numpy as np, torch, torch.nn as nn, cv2
from tools.apk_export_to_dataset import load_export, crops_for_base
S = 112
def aug(img, rng):
    h, w = img.shape[:2]
    # 颜色
    img = img.astype(np.float32)
    img *= rng.uniform(0.85, 1.15)
    img += rng.uniform(-12, 12)
    img = np.clip(img, 0, 255)
    # 几何（轻微）
    ang = rng.uniform(-4, 4); sc = rng.uniform(0.92, 1.08)
    dx = rng.uniform(-4, 4); dy = rng.uniform(-4, 4)
    M = cv2.getRotationMatrix2D((w/2, h/2), ang, sc); M[0,2] += dx; M[1,2] += dy
    img = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return img.astype(np.uint8)
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", required=True)
    ap.add_argument("--img-root", default=os.path.join(BASE, "android", "assets"))
    ap.add_argument("--epochs", type=int, default=26)
    ap.add_argument("--exclude-bases", default="")
    ap.add_argument("--size", type=int, default=112)
    ap.add_argument("--out", default=os.path.join(BASE, "models", "apk_type_cls_aug.pt"))
    ap.add_argument("--report", default=os.path.join(BASE, "out", "apk_type_report_aug.json"))
    a = ap.parse_args()
    bases = []
    for p in a.export.split(","):
        if os.path.exists(p): bases.extend(load_export(p))
    excl = {int(x) for x in a.exclude_bases.split(',') if x.strip() != ''}
    items = []
    for bi, base in enumerate(bases):
        if bi in excl: print('skip base', bi, flush=True); continue
        crops, _ = crops_for_base(base, a.img_root)
        for crop, lab in crops:
            items.append((cv2.resize(crop, (S, S), interpolation=cv2.INTER_AREA), lab["type"], bi))
        print("base", bi, base.get("image"), "crops", len(crops), flush=True)
    types = sorted({t for _, t, _ in items}); TIDX = {t:i for i,t in enumerate(types)}
    print("total", len(items), "types", len(types), flush=True)
    DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("device", DEV, flush=True)
    class Net(nn.Module):
        def __init__(self, n):
            super().__init__()
            def blk(i,o): return nn.Sequential(nn.Conv2d(i,o,3,padding=1), nn.BatchNorm2d(o), nn.ReLU(True), nn.MaxPool2d(2))
            self.f = nn.Sequential(blk(3,32), blk(32,64), blk(64,128), blk(128,192), nn.AdaptiveAvgPool2d(1))
            self.drop = nn.Dropout(0.25); self.head = nn.Linear(192, n)
        def forward(self, x): return self.head(self.drop(self.f(x).flatten(1)))
    rng = random.Random(7)
    def batch(idx, train):
        xs = []
        for i in idx:
            c = items[i][0]
            if train: c = aug(c, rng)
            xs.append(c[:, :, ::-1])
        x = torch.from_numpy(np.stack(xs).copy()).permute(0,3,1,2).float().div(255).to(DEV)
        y = torch.tensor([TIDX[items[i][1]] for i in idx], dtype=torch.long).to(DEV)
        return x, y
    base_ids = sorted({bi for _,_,bi in items})
    reports = []; per_type = {}
    for hold in base_ids:
        tr = [i for i,(_,_,bi) in enumerate(items) if bi != hold]
        va = [i for i,(_,_,bi) in enumerate(items) if bi == hold]
        net = Net(len(types)).to(DEV)
        opt = torch.optim.AdamW(net.parameters(), lr=2e-3, weight_decay=2e-4)
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=a.epochs)
        lossf = nn.CrossEntropyLoss(label_smoothing=0.05)
        for ep in range(a.epochs):
            net.train(); rng.shuffle(tr)
            for i in range(0, len(tr), 48):
                x, y = batch(tr[i:i+48], True)
                loss = lossf(net(x), y); opt.zero_grad(); loss.backward(); opt.step()
            sched.step()
        net.eval(); t1=t3=n=0; corr=0
        with torch.no_grad():
            for i in range(0, len(va), 128):
                x, y = batch(va[i:i+128], False); logits = net(x)
                pred = logits.argmax(1); n += len(y)
                t1 += int((pred==y).sum())
                t3i = logits.topk(min(3,len(types)),1).indices
                t3 += int(sum(1 for k in range(len(y)) if y[k] in t3i[k]))
                for k in range(len(y)):
                    gt = types[int(y[k])]; ok = int(pred[k]==y[k])
                    d = per_type.setdefault(gt, [0,0]); d[0]+=ok; d[1]+=1
        print("hold", hold, "val", n, "top1 %.3f top3 %.3f" % (t1/n, t3/n), flush=True)
        reports.append({"hold": hold, "n": n, "top1": t1/n, "top3": t3/n})
    mean1 = sum(r["top1"] for r in reports)/len(reports)
    print("CV mean top1 %.3f top3 %.3f" % (mean1, sum(r["top3"] for r in reports)/len(reports)))
    rows = sorted(((t, v[0]/v[1], v[1]) for t,v in per_type.items() if v[1]>=3), key=lambda x:-x[1])
    for t, acc, n in rows:
        print("  %-24s %.2f  (n=%d)" % (t, acc, n))
    json.dump({"cv": reports, "cv_mean_top1": mean1,
               "per_type": {t: {"acc": v[0]/v[1], "n": v[1]} for t,v in per_type.items()}},
              open(a.report, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # 全量训练一次保存
    net = Net(len(types)).to(DEV); opt = torch.optim.AdamW(net.parameters(), lr=2e-3, weight_decay=2e-4)
    lossf = nn.CrossEntropyLoss(label_smoothing=0.05)
    allidx = list(range(len(items)))
    for ep in range(a.epochs):
        net.train(); rng.shuffle(allidx)
        for i in range(0, len(allidx), 48):
            x, y = batch(allidx[i:i+48], True)
            loss = lossf(net(x), y); opt.zero_grad(); loss.backward(); opt.step()
    torch.save({"model": net.state_dict(), "types": types, "size": S}, a.out)
    print("saved", a.out)
if __name__ == "__main__":
    main()
