# -*- coding: utf-8 -*-
"""标注清洗 + 重训：
1) 每类内做外观聚类（NCC），保留最大簇（同一种真实建筑应长得一致），丢弃离群（多半是错标）；
2) 再按 TH16 数量上限截断，超出部分保留与簇心最接近的若干条；
3) 用清洗后的集合按原协议（块邻域分组 5 折 × 3 seed）重训。
"""
import json, os, random
from collections import Counter, defaultdict
import numpy as np, cv2
import torch, torch.nn as nn, torch.nn.functional as F
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
HI = os.path.join(BASE, "out", "overlay", "_auto_label", "hi")
MAX = os.path.join(BASE, "out", "overlay", "_recon", "max")
REC = os.path.join(BASE, "out", "overlay", "_recog_b")
SIZE = 96
torch.set_num_threads(8)
CAP = {"town-hall": 1, "clan-castle": 1, "monolith": 1, "eagle-artillery": 1,
       "multi-archer-tower": 2, "scattershot": 2, "ricochet-cannon": 2, "firespitter": 2,
       "air-sweeper": 2, "spell-tower": 2, "inferno-tower": 3, "bomb-tower": 2,
       "x-bow": 4, "air-defense": 4, "hidden-tesla": 5, "wizard-tower": 5, "mortar": 4,
       "archer-tower": 8, "cannon": 7, "gold-mine": 7, "builder-hut": 5, "barracks": 1}


def imread(p): return cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)


class Net(nn.Module):
    def __init__(self, ncls):
        super().__init__()
        def blk(i, o):
            return nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(True),
                                 nn.Conv2d(o, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(True), nn.MaxPool2d(2))
        self.f = nn.Sequential(blk(3, 24), blk(24, 48), blk(48, 96), nn.AdaptiveAvgPool2d(1))
        self.head = nn.Sequential(nn.Flatten(), nn.Dropout(0.35), nn.Linear(96, ncls))
    def forward(self, x): return self.head(self.f(x))


def aug(img, rng):
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), rng.uniform(-8, 8), rng.uniform(0.9, 1.12))
    M[0, 2] += rng.uniform(-10, 10); M[1, 2] += rng.uniform(-10, 10)
    g = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    if rng.random() < 0.8:
        g = np.clip(g.astype(np.float32) * rng.uniform(0.88, 1.12) + rng.uniform(-10, 10), 0, 255).astype(np.uint8)
    return g


def to_tensor(imgs):
    arr = [cv2.resize(g, (SIZE, SIZE), interpolation=cv2.INTER_AREA)[..., ::-1].astype(np.float32) / 255.0 for g in imgs]
    return torch.from_numpy(np.ascontiguousarray(np.stack(arr).transpose(0, 3, 1, 2)))


def train(X, y, ncls, epochs=80, seed=0):
    rng = random.Random(int(seed)); torch.manual_seed(int(seed))
    net = Net(ncls)
    opt = torch.optim.AdamW(net.parameters(), lr=3e-3, weight_decay=2e-3)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    yt = torch.from_numpy(np.array(y, np.int64))
    n, bs = len(X), 18
    for ep in range(epochs):
        net.train(); idx = list(range(n)); rng.shuffle(idx)
        for s in range(0, n, bs):
            sel = idx[s:s + bs]
            opt.zero_grad()
            F.cross_entropy(net(to_tensor([aug(X[i], rng) for i in sel])), yt[sel], label_smoothing=0.05).backward()
            opt.step()
        sched.step()
    net.eval()
    return net


def load_all():
    out = []
    for fn in ("labels_max.json", "labels_max2.json", "labels_max3.json", "labels_max4.json"):
        p = os.path.join(HI, fn)
        if os.path.exists(p):
            out += json.load(open(p, encoding="utf-8"))
    imgs, X, y, blocks = {}, [], [], []
    for r in out:
        b = r["block"]
        if b not in imgs:
            imgs[b] = imread(os.path.join(MAX, b + ".png"))
        img = imgs[b]
        half = 150
        x0 = max(0, min(r["x"] - half, img.shape[1] - 300))
        y0 = max(0, min(r["y"] - half, img.shape[0] - 300))
        c = cv2.resize(img[y0:y0 + 300, x0:x0 + 300], (108, 108), interpolation=cv2.INTER_AREA)
        X.append(c); y.append(r["type"]); blocks.append(b)
    return X, y, blocks, out


def gray_feat(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    g = (g - g.mean()) / (g.std() + 1e-6)
    return g.ravel()


def clean(X, y, rows):
    by = defaultdict(list)
    for i, t in enumerate(y):
        by[t].append(i)
    keep = []
    report = {}
    for t, idxs in sorted(by.items()):
        Fm = np.stack([gray_feat(X[i]) for i in idxs])
        S = (Fm @ Fm.T) / Fm.shape[1]
        # 贪心：以每条为中心统计 0.75 以上邻居，取邻居数最多的中心作为簇，保留其簇成员
        best_center, best_members = None, []
        for a in range(len(idxs)):
            members = [b for b in range(len(idxs)) if a == b or S[a, b] > 0.75]
            if len(members) > len(best_members):
                best_center, best_members = a, members
        kept = [idxs[b] for b in best_members]
        cap = CAP.get(t, 99)
        kept = kept[:cap]
        report[t] = {"raw": len(idxs), "cluster": len(best_members), "kept": len(kept), "cap": cap}
        keep += kept
    return keep, report


def main():
    X, y, blocks, rows = load_all()
    keep, report = clean(X, y, rows)
    print("raw=%d kept=%d" % (len(y), len(keep)), flush=True)
    for t, r in report.items():
        print("  %-20s raw=%-2d cluster=%-2d kept=%-2d cap=%s" % (t, r["raw"], r["cluster"], r["kept"], r["cap"]), flush=True)
    Xc = [X[i] for i in keep]
    yc = [y[i] for i in keep]
    bc = [blocks[i] for i in keep]
    classes = sorted(set(yc))
    print("classes=%d" % len(classes), flush=True)
    print("counts=", dict(Counter(yc)), flush=True)
    buckets = sorted(set((int(b.split("c")[1][0]) // 2, int(b.split("r")[1]) // 2) for b in bc))
    rng = random.Random(7); bl = buckets[:]; rng.shuffle(bl)
    assign = {b: i % 5 for i, b in enumerate(bl)}
    fold_of = [assign[(int(b.split("c")[1][0]) // 2, int(b.split("r")[1]) // 2)] for b in bc]
    accs = []
    for run in range(3):
        pred = [None] * len(yc)
        for f in range(5):
            te = [i for i in range(len(yc)) if fold_of[i] == f]
            tr = [i for i in range(len(yc)) if fold_of[i] != f]
            if not te or not tr:
                continue
            net = train([Xc[i] for i in tr], [classes.index(yc[i]) for i in tr], len(classes), seed=run * 10 + f)
            prob = F.softmax(net(to_tensor([Xc[i] for i in te])), 1).numpy()
            for j, i in enumerate(te):
                pred[i] = classes[int(np.argmax(prob[j]))]
        ok = [i for i in range(len(yc)) if pred[i] is not None]
        acc = float(np.mean([pred[i] == yc[i] for i in ok]))
        accs.append(acc)
        print("seed %d acc=%.3f (n=%d)" % (run, acc, len(ok)), flush=True)
    res = {"raw": len(y), "kept": len(keep), "report": report,
           "counts": dict(Counter(yc)), "acc_per_seed": accs,
           "acc_mean": float(np.mean(accs)), "acc_std": float(np.std(accs))}
    json.dump(res, open(os.path.join(REC, "max_model_clean_result.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "report"}, ensure_ascii=False))


main()
