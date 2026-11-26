# -*- coding: utf-8 -*-
"""训练「类型 + 等级」双头模型（合成素材数据集）。

    python tools/train_synth_level.py --epochs 120
产物：models/synth_level.pt + models/synth_level_metrics.json
"""
import argparse, json, os, random, sys
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DATA = r"E:\ClashLab\datasets\synth_level"
SIZE = 96


class Net(nn.Module):
    def __init__(self, n_types):
        super().__init__()
        def blk(i, o):
            return nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(True), nn.MaxPool2d(2))
        self.f = nn.Sequential(blk(3, 24), blk(24, 48), blk(48, 96), blk(96, 128), nn.AdaptiveAvgPool2d(1))
        self.drop = nn.Dropout(0.2)
        self.type_head = nn.Linear(128, n_types)
        self.level_head = nn.Linear(128, 1)

    def forward(self, x):
        h = self.drop(self.f(x).flatten(1))
        return self.type_head(h), torch.sigmoid(self.level_head(h)).squeeze(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=120)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    ap.add_argument("--amp", action="store_true", default=True)
    ap.add_argument("--lr", type=float, default=1.2e-3)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--models-dir", default=os.path.join(ROOT, "models"))
    a = ap.parse_args()
    torch.set_num_threads(min(os.cpu_count() or 4, 8))
    use_cuda = torch.cuda.is_available() and a.device in ("auto", "cuda")
    dev = torch.device("cuda" if use_cuda else "cpu")
    print("[device]", dev, "| cuda:", torch.version.cuda, flush=True)
    rng = random.Random(a.seed); np.random.seed(a.seed); torch.manual_seed(a.seed)

    imgs = np.load(os.path.join(DATA, "imgs.npy"))
    labels = json.load(open(os.path.join(DATA, "labels.json"), encoding="utf-8"))
    types = sorted({l["type"] for l in labels})
    tidx = {t: i for i, t in enumerate(types)}
    y_t = np.array([tidx[l["type"]] for l in labels], np.int64)
    y_l = np.array([l["level"] / max(1, l["max_level"]) for l in labels], np.float32)
    y_lv = np.array([l["level"] for l in labels], np.float32)
    mx = np.array([l["max_level"] for l in labels], np.float32)
    n = len(labels)
    perm = np.random.RandomState(a.seed).permutation(n)
    n_val = max(200, int(n * 0.1))
    val = perm[:n_val]; tr = perm[n_val:]
    X = np.transpose(imgs.astype(np.float32) / 255.0, (0, 3, 1, 2))
    X_t = torch.from_numpy(X[tr]); X_v = torch.from_numpy(X[val])
    yt_t = torch.from_numpy(y_t[tr]).to(dev); yl_t = torch.from_numpy(y_l[tr]).to(dev)
    yt_v = torch.from_numpy(y_t[val]).to(dev); yl_v = torch.from_numpy(y_l[val]).to(dev)
    X_v = X_v.to(dev)
    print("[data] n=%d train=%d val=%d types=%d" % (n, len(tr), len(val), len(types)), flush=True)
    net = Net(len(types)).to(dev)
    opt = torch.optim.AdamW(net.parameters(), lr=a.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=a.epochs)
    for ep in range(a.epochs):
        net.train()
        idx = torch.randperm(len(tr))
        tot, nb = 0.0, 0
        for s in range(0, len(tr), a.batch):
            b = idx[s:s + a.batch]
            xb = X_t[b].to(dev, non_blocking=True)
            if random.random() < 0.5:
                xb = torch.flip(xb, dims=[3])
            with torch.autocast(device_type=dev.type, dtype=torch.bfloat16, enabled=use_cuda):
                logits, lv = net(xb)
            loss = F.cross_entropy(logits.float(), yt_t[b]) + 2.0 * F.smooth_l1_loss(lv.float(), yl_t[b])
            opt.zero_grad(); loss.backward(); opt.step()
            tot += float(loss); nb += 1
        sched.step()
        if ep % 10 == 0 or ep == a.epochs - 1:
            net.eval()
            with torch.no_grad():
                logits, lv = net(X_v)
                acc = float((logits.argmax(1) == yt_v).float().mean())
                pred_lv = lv.detach().cpu().numpy() * mx[val]
                mae = float(np.mean(np.abs(pred_lv - y_lv[val])))
            print("[train] ep=%d loss=%.4f val_type_acc=%.3f val_level_mae=%.2f" % (ep, tot / max(1, nb), acc, mae), flush=True)
    net.eval()
    with torch.no_grad():
        logits, lv = net(X_v)
        acc = float((logits.argmax(1) == yt_v).float().mean())
        pred_lv = lv.detach().cpu().numpy() * mx[val]
        mae = float(np.mean(np.abs(pred_lv - y_lv[val])))
        per_type = {}
        for t in types:
            m = np.array([labels[i]["type"] == t for i in val])
            if m.sum() > 0:
                per_type[t] = round(float(np.mean(np.abs(pred_lv[m] - y_lv[val][m]))), 2)
    metrics = {"n": n, "train": len(tr), "val": len(val), "types": len(types), "epochs": a.epochs,
               "type_acc": round(acc, 4), "level_mae": round(mae, 3), "per_type_level_mae": per_type}
    os.makedirs(a.models_dir, exist_ok=True)
    torch.save({"state_dict": net.state_dict(), "types": types, "input_size": SIZE, "metrics": metrics},
               os.path.join(a.models_dir, "synth_level.pt"))
    json.dump(metrics, open(os.path.join(a.models_dir, "synth_level_metrics.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("[metrics]", json.dumps({k: metrics[k] for k in ("type_acc", "level_mae")}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
