# -*- coding: utf-8 -*-
"""高倍（~70px/格）标注样本 → 跨域测试：战场 107 栋训练 → 高倍自家村庄测试。"""
import json, os, sys, random
import numpy as np, cv2
import torch, torch.nn as nn, torch.nn.functional as F
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
HI = os.path.join(BASE, "out", "overlay", "_auto_label", "hi")
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
    M[0, 2] += rng.uniform(-8, 8); M[1, 2] += rng.uniform(-8, 8)
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
    n, bs = len(X), 24
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


def load_battle():
    js = json.load(open(os.path.join(BASE, "out", "overlay", "_quad_calib", "summary.json"), encoding="utf-8"))
    crops, ys = [], []
    S, WIN = 24, 4.5
    W = int(round(S * WIN))
    for b in ["03", "05", "06"]:
        frame = imread(os.path.join(BASE, "bases", "th16", b, "base.png"))
        H = np.array(js[b]["H"], np.float64)
        lay = json.load(open(os.path.join(BASE, "bases", "th16", b, "layout.json"), encoding="utf-8"))
        for bd in lay["buildings"]:
            tx, ty = bd["tile"]
            Fm = H @ np.array([[1.0 / S, 0, tx - WIN / 2], [0, 1.0 / S, ty - WIN / 2], [0, 0, 1]])
            p = cv2.warpPerspective(frame, np.linalg.inv(Fm), (W, W), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            crops.append(cv2.resize(p, (108, 108), interpolation=cv2.INTER_AREA)); ys.append(bd["type"])
    return crops, np.array(ys)


def load_hi():
    labels = json.load(open(os.path.join(HI, "labels_hi.json"), encoding="utf-8"))
    imgs = {}
    crops, ys, meta = [], [], []
    for r in labels:
        v = r["view"]
        if v not in imgs:
            imgs[v] = imread(os.path.join(HI, v + ".png"))
        img = imgs[v]
        half = 150
        c = img[max(0, r["y"] - half):r["y"] + half, max(0, r["x"] - half):r["x"] + half]
        if c.shape[0] < 100 or c.shape[1] < 100:
            continue
        crops.append(cv2.resize(c, (108, 108), interpolation=cv2.INTER_AREA))
        ys.append(r["type"]); meta.append(r)
    return crops, np.array(ys), meta


def main():
    Xb, yb = load_battle()
    Xh, yh, meta = load_hi()
    classes = sorted(set(yb) | set(yh))
    net = train(Xb, [classes.index(t) for t in yb], len(classes), epochs=100, seed=3)
    with torch.no_grad():
        prob = F.softmax(net(to_tensor(Xh)), 1).numpy()
    pred = [classes[int(np.argmax(p))] for p in prob]
    known = [i for i in range(len(yh)) if yh[i] in set(yb)]
    acc_all = float(np.mean([pred[i] == yh[i] for i in range(len(yh))]))
    acc_known = float(np.mean([pred[i] == yh[i] for i in known])) if known else float("nan")
    rows = [{"view": meta[i]["view"], "x": meta[i]["x"], "y": meta[i]["y"],
             "truth": str(yh[i]), "pred": pred[i]} for i in range(len(yh))]
    res = {"n_battle": len(yb), "n_hi": len(yh), "known_n": len(known),
           "acc_all_hi": acc_all, "acc_known_hi": acc_known,
           "subset": rows,
           "note": "高倍标注仅 18 条且含非防御类；known_n 才是同类可比样本"}
    json.dump(res, open(os.path.join(REC, "cross_hi_result.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("n_hi=%d known=%d acc_all=%.3f acc_known=%.3f" % (len(yh), len(known), acc_all, acc_known))
    for r in rows:
        print("%s(%d,%d) truth=%s pred=%s" % (r["view"], r["x"], r["y"], r["truth"], r["pred"]))


main()
