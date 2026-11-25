# -*- coding: utf-8 -*-
"""A 执行：最大档（侦察 ~70px/格）专用模型训练与分组评估。

数据：hi/labels_max.json（17 条）+ hi/labels_max2.json（25 条）= 42 条
评估：按块邻域分组 5 折（相邻块同折，减少同一建筑跨块泄漏），3 seed 平均。
对照：战场训练→最大档测试 0.118/0.182（cross_max_result.json）。
"""
import json, os, random
import numpy as np, cv2
import torch, torch.nn as nn, torch.nn.functional as F
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
HI = os.path.join(BASE, "out", "overlay", "_auto_label", "hi")
MAX = os.path.join(BASE, "out", "overlay", "_recon", "max")
REC = os.path.join(BASE, "out", "overlay", "_recog_b")
SIZE = 96
torch.set_num_threads(8)


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


def train(X, y, ncls, epochs=90, seed=0):
    rng = random.Random(int(seed)); torch.manual_seed(int(seed))
    net = Net(ncls)
    opt = torch.optim.AdamW(net.parameters(), lr=3e-3, weight_decay=2e-3)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    yt = torch.from_numpy(np.array(y, np.int64))
    n, bs = len(X), 20
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


@torch.no_grad()
def predict(net, imgs):
    return F.softmax(net(to_tensor(imgs)), 1).numpy()


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
        c = img[y0:y0 + 300, x0:x0 + 300]
        X.append(cv2.resize(c, (108, 108), interpolation=cv2.INTER_AREA))
        y.append(r["type"]); blocks.append(b)
    return X, np.array(y), blocks


def main():
    X, y, blocks = load_all()
    classes = sorted(set(y))
    from collections import Counter
    print("n=%d classes=%d" % (len(y), len(classes)), flush=True)
    print("counts=", dict(Counter(y)), flush=True)
    # 块邻域分组：相邻块同折
    buckets = sorted(set((int(b.split("c")[1][0]) // 2, int(b.split("r")[1]) // 2) for b in blocks))
    rng = random.Random(7); bl = buckets[:]; rng.shuffle(bl)
    assign_bucket = {b: i % 5 for i, b in enumerate(bl)}
    fold_of = [assign_bucket[(int(b.split("c")[1][0]) // 2, int(b.split("r")[1]) // 2)] for b in blocks]
    seeds = [11, 22, 33]
    accs = []
    for seed in seeds:
        pred = [None] * len(y)
        for f in range(5):
            te = [i for i in range(len(y)) if fold_of[i] == f]
            tr = [i for i in range(len(y)) if fold_of[i] != f]
            if not te or not tr:
                continue
            net = train([X[i] for i in tr], [classes.index(y[i]) for i in tr], len(classes), seed=seed * 10 + f)
            prob = predict(net, [X[i] for i in te])
            for j, i in enumerate(te):
                pred[i] = classes[int(np.argmax(prob[j]))]
        ok = [i for i in range(len(y)) if pred[i] is not None]
        acc = float(np.mean([pred[i] == y[i] for i in ok]))
        accs.append(acc)
        print("seed %d acc=%.3f (n_eval=%d)" % (seed, acc, len(ok)), flush=True)
    res = {"n": int(len(y)), "classes": classes, "class_counts": dict(Counter(y)),
           "acc_per_seed": accs, "acc_mean": float(np.mean(accs)), "acc_std": float(np.std(accs)),
           "protocol": "最大档专用，块邻域分组 5 折 × 3 seed",
           "baseline_battle_same_zoom": 0.523, "baseline_cross_domain": 0.118}
    json.dump(res, open(os.path.join(REC, "max_model_result.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False))


main()
