# -*- coding: utf-8 -*-
"""27px v2a：基线小网 + 强增强 + TTA + 类权重（隔离「增强/TTA/权重」的收益，跑得快）。
协议：同阵 5 折 + 留一阵（与 cnn_lob.py 一致，n=107 / 18 类 / 基线 0.523 / LOBO 0.520）。
"""
import json, os, random, sys
import numpy as np, cv2
import torch, torch.nn as nn, torch.nn.functional as F

ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(ROOT, "out", "overlay", "_recog_b")
BASES = ["03", "05", "06"]
S = 24
WIN_T = 4.5
SIZE = 96


def imread_u(p): return cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)


def build():
    js = json.load(open(os.path.join(ROOT, "out", "overlay", "_quad_calib", "summary.json"), encoding="utf-8"))
    ps, ys, bs = [], [], []
    W = int(round(S * WIN_T))
    for b in BASES:
        frame = imread_u(os.path.join(ROOT, "bases", "th16", b, "base.png"))
        H = np.array(js[b]["H"], np.float64)
        lay = json.load(open(os.path.join(ROOT, "bases", "th16", b, "layout.json"), encoding="utf-8"))
        for bd in lay["buildings"]:
            tx, ty = bd["tile"]
            Fm = H @ np.array([[1.0 / S, 0, tx - WIN_T / 2], [0, 1.0 / S, ty - WIN_T / 2], [0, 0, 1]])
            ps.append(cv2.warpPerspective(frame, np.linalg.inv(Fm), (W, W), flags=cv2.INTER_LINEAR,
                                          borderMode=cv2.BORDER_REPLICATE))
            ys.append(bd["type"]); bs.append(b)
    return ps, np.array(ys), np.array(bs)


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
    M = cv2.getRotationMatrix2D((w / 2, h / 2), rng.uniform(-12, 12), rng.uniform(0.82, 1.20))
    M[0, 2] += rng.uniform(-14, 14); M[1, 2] += rng.uniform(-14, 14)
    g = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    if rng.random() < 0.8:
        g = np.clip(g.astype(np.float32) * rng.uniform(0.80, 1.22) + rng.uniform(-16, 16), 0, 255).astype(np.uint8)
    if rng.random() < 0.35:
        ga = rng.uniform(0.7, 1.4)
        g = np.clip(((g / 255.0) ** ga) * 255.0, 0, 255).astype(np.uint8)
    if rng.random() < 0.35:
        hsv = cv2.cvtColor(g, cv2.COLOR_BGR2HSV)
        hsv[..., 0] = (hsv[..., 0].astype(np.int16) + rng.randint(-12, 12)) % 180
        hsv[..., 1] = np.clip(hsv[..., 1].astype(np.float32) * rng.uniform(0.82, 1.18), 0, 255)
        g = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    if rng.random() < 0.3:
        cs = rng.randint(6, 16); x0 = rng.randint(0, w - cs); y0 = rng.randint(0, h - cs)
        g[y0:y0 + cs, x0:x0 + cs] = 0
    return cv2.resize(g, (SIZE, SIZE), interpolation=cv2.INTER_AREA)


def tta(img):
    out = [img]
    for ang, sc in ((6.0, 1.06), (-6.0, 0.95)):
        M = cv2.getRotationMatrix2D((img.shape[1] / 2, img.shape[0] / 2), ang, sc)
        out.append(cv2.warpAffine(img, M, (img.shape[1], img.shape[0]), flags=cv2.INTER_LINEAR,
                                  borderMode=cv2.BORDER_REPLICATE))
    return out


def tensor(imgs):
    arr = [cv2.resize(g, (SIZE, SIZE), interpolation=cv2.INTER_AREA)[..., ::-1].astype(np.float32) / 255.0 for g in imgs]
    return torch.from_numpy(np.ascontiguousarray(np.stack(arr).transpose(0, 3, 1, 2)))


def train_predict(Xtr, ytr, Xte, ncls, epochs=100, seed=0, w=None):
    seed = int(seed); rng = random.Random(seed); torch.manual_seed(seed)
    net = Net(ncls)
    opt = torch.optim.AdamW(net.parameters(), lr=3e-3, weight_decay=2e-3)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    yt = torch.from_numpy(np.asarray(ytr, np.int64))
    n, bs = len(Xtr), 24
    for ep in range(epochs):
        net.train(); idx = list(range(n)); rng.shuffle(idx)
        for s in range(0, n, bs):
            sel = idx[s:s + bs]
            opt.zero_grad()
            F.cross_entropy(net(tensor([aug(Xtr[i], rng) for i in sel])), yt[sel],
                            label_smoothing=0.1, weight=w).backward()
            opt.step()
        sched.step()
    net.eval()
    probs = []
    with torch.no_grad():
        for v in range(3):
            probs.append(F.softmax(net(tensor([tta(x)[v] for x in Xte])), 1).numpy())
    return np.argmax(sum(probs), axis=1)


def strat_folds(y, k=5, seed=7):
    rng = np.random.default_rng(seed); folds = np.zeros(len(y), int)
    for t in sorted(set(y)):
        idx = np.where(y == t)[0]; rng.shuffle(idx); folds[idx] = np.arange(len(idx)) % k
    return folds


def main():
    seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    epochs = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    ps, y, bs = build()
    classes = sorted(set(y)); cmap = {c: i for i, c in enumerate(classes)}
    yi = np.array([cmap[t] for t in y])
    cnt = np.bincount(yi, minlength=len(classes))
    w = torch.from_numpy((1.0 / np.sqrt(np.maximum(cnt, 1))).astype(np.float32))
    w = w / w.mean()
    print("n=%d classes=%d seeds=%d epochs=%d majority=%.3f" % (len(y), len(classes), seeds, epochs,
                                                               cnt.max() / len(y)), flush=True)
    folds = strat_folds(y)
    win, lobo = [], []
    for seed in range(seeds):
        yp = np.array([-1] * len(y))
        for f in sorted(set(folds)):
            te = folds == f; tr = ~te
            yp[te] = train_predict([ps[i] for i in np.where(tr)[0]], yi[tr],
                                   [ps[i] for i in np.where(te)[0]], len(classes), epochs, 100 + f + seed * 7, w)
        win.append(float((yp == yi).mean())); print("  seed %d within=%.3f" % (seed, win[-1]), flush=True)
        yt2, yp2 = [], []
        for b in BASES:
            te = bs == b; tr = ~te
            keep = np.array([t in set(y[tr]) for t in y[te]])
            pr = train_predict([ps[i] for i in np.where(tr)[0]], yi[tr],
                               [ps[i] for i in np.where(te)[0]], len(classes), epochs, 7 + seed, w)
            yt2 += list(yi[te][keep]); yp2 += list(pr[keep])
        lobo.append(float((np.array(yt2) == np.array(yp2)).mean()))
        print("  seed %d lobo=%.3f (n=%d)" % (seed, lobo[-1], len(yt2)), flush=True)
    res = {"n": int(len(y)), "classes": len(classes), "epochs": epochs,
           "within_mean": float(np.mean(win)), "within_all": win,
           "lobo_mean": float(np.mean(lobo)), "lobo_all": lobo,
           "majority": float(cnt.max() / len(y)), "baseline_within": 0.5234, "baseline_lobo": 0.520}
    json.dump(res, open(os.path.join(OUT, "cnn_lobo2a_result.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False), flush=True)


main()
