# -*- coding: utf-8 -*-
"""用「标注 layout」训练 27px 识别模型（同阵 5 折 + 留一阵）。

    python tools/train_from_annotations.py --layouts bases/th16/*/layout.json out/annotate/*.json

每次标注新增的数据（out/annotate/*.json）都会被 recog_dataset 读入，直接参与训练与评估。
"""
import argparse
import glob
import json
import os
import random
import sys

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from clashlab.recog_dataset import build_dataset  # noqa: E402

OUT = os.path.join(ROOT, "out", "recog")


class Net(nn.Module):
    def __init__(self, ncls):
        super().__init__()
        def blk(i, o):
            return nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(True),
                                 nn.Conv2d(o, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(True), nn.MaxPool2d(2))
        self.f = nn.Sequential(blk(3, 24), blk(24, 48), blk(48, 96), nn.AdaptiveAvgPool2d(1))
        self.head = nn.Sequential(nn.Flatten(), nn.Dropout(0.35), nn.Linear(96, ncls))

    def forward(self, x):
        return self.head(self.f(x))


def aug(img, rng):
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), rng.uniform(-8, 8), rng.uniform(0.9, 1.1))
    M[0, 2] += rng.uniform(-8, 8); M[1, 2] += rng.uniform(-8, 8)
    g = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    if rng.random() < 0.7:
        g = np.clip(g.astype(np.float32) * rng.uniform(0.88, 1.12) + rng.uniform(-10, 10), 0, 255).astype(np.uint8)
    if rng.random() < 0.2:
        cs = rng.randint(8, 18); x0 = rng.randint(0, w - cs); y0 = rng.randint(0, h - cs)
        g[y0:y0 + cs, x0:x0 + cs] = 0
    return g


def tensor(imgs):
    arr = [g[..., ::-1].astype(np.float32) / 255.0 for g in imgs]
    return torch.from_numpy(np.ascontiguousarray(np.stack(arr).transpose(0, 3, 1, 2)))


def train_predict(Xtr, ytr, Xte, ncls, epochs, seed, w):
    seed = int(seed)
    rng = random.Random(seed); torch.manual_seed(seed)
    net = Net(ncls)
    opt = torch.optim.AdamW(net.parameters(), lr=3e-3, weight_decay=2e-3)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    yt = torch.from_numpy(np.asarray(ytr, np.int64))
    n, bs = len(Xtr), 24
    for ep in range(epochs):
        net.train(); idx = list(range(n)); rng.shuffle(idx)
        for s in range(0, n, bs):
            sel = idx[s:s + bs]
            xb = tensor([aug(Xtr[i], rng) for i in sel])
            opt.zero_grad()
            F.cross_entropy(net(xb), yt[sel], label_smoothing=0.05, weight=w).backward()
            opt.step()
        sched.step()
    net.eval()
    with torch.no_grad():
        return net(tensor(Xte)).argmax(1).numpy()


def strat_folds(y, k=5, seed=7):
    rng = np.random.default_rng(seed); folds = np.zeros(len(y), int)
    for t in sorted(set(y)):
        idx = np.where(y == t)[0]; rng.shuffle(idx); folds[idx] = np.arange(len(idx)) % k
    return folds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layouts", nargs="+", required=True)
    ap.add_argument("--epochs", type=int, default=120)
    ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    global cv2
    import cv2
    paths = []
    for pat in a.layouts:
        paths += sorted(glob.glob(pat))
    ps, labels, bases = build_dataset(paths)
    if not ps:
        raise SystemExit("没有可用样本（layout.json 缺 quad 或 base.png）")
    classes = sorted(set(labels))
    cmap = {c: i for i, c in enumerate(classes)}
    yi = np.array([cmap[t] for t in labels])
    bs = np.array(bases)
    cnt = np.bincount(yi, minlength=len(classes))
    w = torch.from_numpy((1.0 / np.sqrt(np.maximum(cnt, 1))).astype(np.float32)); w = w / w.mean()
    print("n=%d bases=%d classes=%d epoch=%d majority=%.3f" % (
        len(ys := labels), len(set(bases)), len(classes), a.epochs, cnt.max() / len(ys)), flush=True)
    folds = strat_folds(yi)
    win, lobo = [], []
    for seed in range(a.seeds):
        yp = np.array([-1] * len(yi))
        for f in sorted(set(folds)):
            te = folds == f; tr = ~te
            yp[te] = train_predict([ps[i] for i in np.where(tr)[0]], yi[tr],
                                   [ps[i] for i in np.where(te)[0]], len(classes), a.epochs,
                                   int(100 + int(f) + seed * 7), w)
        win.append(float((yp == yi).mean())); print("  seed %d within=%.3f" % (seed, win[-1]), flush=True)
        yt2, yp2 = [], []
        for b in sorted(set(bases)):
            te = bs == b; tr = ~te
            if not te.any() or not tr.any():
                continue
            keep = np.array([t in set(np.array(labels)[tr]) for t in np.array(labels)[te]])
            pr = train_predict([ps[i] for i in np.where(tr)[0]], yi[tr],
                               [ps[i] for i in np.where(te)[0]], len(classes), a.epochs, 7 + seed, w)
            yt2 += list(yi[te][keep]); yp2 += list(pr[keep])
        lobo.append(float((np.array(yt2) == np.array(yp2)).mean()))
        print("  seed %d lobo=%.3f (n=%d)" % (seed, lobo[-1], len(yt2)), flush=True)
    os.makedirs(a.out, exist_ok=True)
    res = {"n": len(ys), "bases": len(set(bases)), "classes": len(classes), "epochs": a.epochs,
           "within_mean": float(np.mean(win)), "within_all": win,
           "lobo_mean": float(np.mean(lobo)), "lobo_all": lobo, "majority": float(cnt.max() / len(ys))}
    json.dump(res, open(os.path.join(a.out, "train_from_annotations.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False), flush=True)


main()
