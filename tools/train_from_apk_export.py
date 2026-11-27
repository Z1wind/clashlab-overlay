# -*- coding: utf-8 -*-
"""一条命令：APK 导出 JSON -> 数据集 -> 训练类型分类器 -> 留一基评估报告。

用法:
  python tools/train_from_apk_export.py --export out/apk_qa/annot_all.json --epochs 12
"""
import argparse, json, os, random, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import numpy as np, torch, torch.nn as nn
from tools.apk_export_to_dataset import load_export, crops_for_base

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", required=True, help="单张 JSON / bundle JSON；逗号分隔多个")
    ap.add_argument("--img-root", default=os.path.join(BASE, "android", "assets"))
    ap.add_argument("--epochs", type=int, default=12)
    ap.add_argument("--out", default=os.path.join(BASE, "models", "apk_type_cls.pt"))
    ap.add_argument("--report", default=os.path.join(BASE, "out", "apk_type_report.json"))
    a = ap.parse_args()
    bases = []
    for p in a.export.split(","):
        p = p.strip()
        if not os.path.exists(p):
            print("skip missing:", p); continue
        bases.extend(load_export(p))
    if not bases:
        print("no exports"); return 2
    items = []  # (crop, type, base_idx)
    for bi, base in enumerate(bases):
        crops, _ = crops_for_base(base, a.img_root)
        for crop, lab in crops:
            items.append((crop, lab["type"], bi))
        print("base", bi, base.get("image"), "crops", len(crops), flush=True)
    types = sorted({t for _, t, _ in items})
    if len(types) < 2 or len(items) < 30:
        print("WARN: 样本太少（%d 张 / %d 类），结果仅供参考" % (len(items), len(types)))
    TIDX = {t: i for i, t in enumerate(types)}
    print("total crops:", len(items), "types:", len(types), flush=True)
    DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    class Net(nn.Module):
        def __init__(self, n):
            super().__init__()
            def blk(i, o): return nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(True), nn.MaxPool2d(2))
            self.f = nn.Sequential(blk(3, 32), blk(32, 64), blk(64, 128), blk(128, 192), nn.AdaptiveAvgPool2d(1))
            self.drop = nn.Dropout(0.2); self.head = nn.Linear(192, n)
        def forward(self, x): return self.head(self.drop(self.f(x).flatten(1)))
    def batch(idx):
        xs = np.stack([items[i][0] for i in idx])[:, :, :, ::-1]
        x = torch.from_numpy(xs.copy()).permute(0, 3, 1, 2).float().div(255).to(DEV)
        y = torch.tensor([TIDX[items[i][1]] for i in idx], dtype=torch.long).to(DEV)
        return x, y
    reports = []
    base_ids = sorted({bi for _, _, bi in items})
    for hold in base_ids:
        tr = [i for i, (_, _, bi) in enumerate(items) if bi != hold]
        va = [i for i, (_, _, bi) in enumerate(items) if bi == hold]
        if len(tr) < 16 or len(va) < 4:
            print("hold base", hold, "skipped (train %d / val %d)" % (len(tr), len(va))); continue
        net = Net(len(types)).to(DEV)
        opt = torch.optim.AdamW(net.parameters(), lr=2e-3, weight_decay=1e-4)
        lossf = nn.CrossEntropyLoss()
        for ep in range(a.epochs):
            net.train(); random.shuffle(tr)
            for i in range(0, len(tr), 64):
                x, y = batch(tr[i:i + 64])
                loss = lossf(net(x), y); opt.zero_grad(); loss.backward(); opt.step()
        net.eval(); top1 = top3 = n = 0
        with torch.no_grad():
            for i in range(0, len(va), 128):
                x, y = batch(va[i:i + 128]); logits = net(x)
                pred = logits.argmax(1); n += len(va[i:i + 128])
                top1 += int((pred == y).sum()); 
                t3 = logits.topk(min(3, len(types)), 1).indices
                top3 += int(sum(1 for k in range(len(y)) if y[k] in t3[k]))
        print("hold base %d: val=%d top1=%.3f top3=%.3f" % (hold, len(va), top1 / n, top3 / n), flush=True)
        reports.append({"hold": hold, "n": n, "top1": top1 / n, "top3": top3 / n})
    if reports:
        mean = sum(r["top1"] for r in reports) / len(reports)
        print("CV mean top1: %.3f" % mean)
    net = Net(len(types)).to(DEV)
    opt = torch.optim.AdamW(net.parameters(), lr=2e-3, weight_decay=1e-4); lossf = nn.CrossEntropyLoss()
    allidx = list(range(len(items)))
    for ep in range(a.epochs):
        net.train(); random.shuffle(allidx)
        for i in range(0, len(allidx), 64):
            x, y = batch(allidx[i:i + 64])
            loss = lossf(net(x), y); opt.zero_grad(); loss.backward(); opt.step()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    torch.save({"model": net.state_dict(), "types": types}, a.out)
    os.makedirs(os.path.dirname(a.report), exist_ok=True)
    json.dump({"bases": len(bases), "crops": len(items), "types": types, "cv": reports,
               "cv_mean_top1": (sum(r["top1"] for r in reports) / len(reports)) if reports else None},
              open(a.report, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("saved", a.out, "| report", a.report)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
