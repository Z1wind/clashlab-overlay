# -*- coding: utf-8 -*-
"""训练「建筑/背景」二分类门控：正样本=合成建筑裁剪，负样本=真实截图边缘背景裁剪。"""
import json, os, random, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np, torch, torch.nn as nn
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("device:", DEV, flush=True)
pos = np.load(os.path.join(BASE, "datasets", "synth_level", "imgs.npy"), mmap_mode="r")
neg = np.load(os.path.join(BASE, "datasets", "bg_negatives", "imgs.npy"))
print("pos:", pos.shape, "neg:", neg.shape, flush=True)
rng = np.random.RandomState(7)
pos_idx = rng.permutation(len(pos))[:12000]
neg_idx = rng.permutation(len(neg))[:4000]
n_val_p = 1200; n_val_n = 400
train = [(int(i), 1) for i in pos_idx[n_val_p:]] + [(int(i), 0) for i in neg_idx[n_val_n:]]
val = [(int(i), 1) for i in pos_idx[:n_val_p]] + [(int(i), 0) for i in neg_idx[:n_val_n]]
print("train:", len(train), "val:", len(val), flush=True)

class Net(nn.Module):
    def __init__(self):
        super().__init__()
        def blk(i, o):
            return nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(True), nn.MaxPool2d(2))
        self.f = nn.Sequential(blk(3, 24), blk(24, 48), blk(48, 96), blk(96, 128), nn.AdaptiveAvgPool2d(1))
        self.drop = nn.Dropout(0.2)
        self.head = nn.Linear(128, 2)
    def forward(self, x):
        return self.head(self.drop(self.f(x).flatten(1)))

def batch(items):
    xs, ys = [], []
    for idx, lab in items:
        arr = pos[idx] if lab == 1 else neg[idx]
        xs.append(arr[:, :, ::-1].copy()); ys.append(lab)
    x = torch.from_numpy(np.stack(xs)).permute(0, 3, 1, 2).float().div(255)
    return x.to(DEV), torch.tensor(ys, dtype=torch.long).to(DEV)

net = Net().to(DEV)
opt = torch.optim.AdamW(net.parameters(), lr=2e-3)
lossf = nn.CrossEntropyLoss()
BS = 128
t0 = time.time(); best_acc = 0.0
for ep in range(6):
    random.shuffle(train)
    tot = n = 0
    for i in range(0, len(train) - BS + 1, BS):
        x, y = batch(train[i:i + BS])
        loss = lossf(net(x), y)
        opt.zero_grad(); loss.backward(); opt.step()
        tot += float(loss.detach()); n += 1
        if n % 30 == 0:
            print("ep%d it%d loss=%.3f (%.0fs)" % (ep, n, tot / n, time.time() - t0), flush=True)
    # val
    net.eval(); correct = 0; conf = np.zeros((2, 2), np.int64)
    with torch.no_grad():
        for i in range(0, len(val), BS):
            x, y = batch(val[i:i + BS])
            pred = net(x).argmax(1)
            for t_, p_ in zip(y.cpu().numpy(), pred.cpu().numpy()):
                conf[t_, p_] += 1
    acc = (conf[0, 0] + conf[1, 1]) / max(1, conf.sum())
    net.train()
    print("epoch", ep + 1, "val_acc=%.4f" % acc, "confusion", conf.tolist(), flush=True)
    if acc > best_acc:
        best_acc = acc
        torch.save({"model": net.state_dict(), "acc": float(acc), "size": 96,
                    "note": "building gate: pos=synth sprites, neg=real bg edges"}, os.path.join(BASE, "models", "building_gate.pt"))
print("TRAIN_DONE best_acc", round(best_acc, 4), flush=True)
