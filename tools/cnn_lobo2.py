# -*- coding: utf-8 -*-
"""27px 同档识别 v2：更强网络 + 更强增强 + TTA + 类权重，协议与基线一致（同阵 5 折 + 留一阵）。
基线（cnn_lob.py）：n=107 / 18 类 / within 0.523 / LOBO 0.520。
"""
import json, os, random, sys
import numpy as np, cv2
import torch, torch.nn as nn, torch.nn.functional as F

ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(ROOT, "out", "overlay", "_recog_b")
BASES = ["03", "05", "06"]
S = 24
SIZE = 96


def imread_u(p): return cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)


def build(win_t=4.5):
    js = json.load(open(os.path.join(ROOT, "out", "overlay", "_quad_calib", "summary.json"), encoding="utf-8"))
    ps, ys, bs = [], [], []
    W = int(round(S * win_t))
    for b in BASES:
        frame = imread_u(os.path.join(ROOT, "bases", "th16", b, "base.png"))
        H = np.array(js[b]["H"], np.float64)
        lay = json.load(open(os.path.join(ROOT, "bases", "th16", b, "layout.json"), encoding="utf-8"))
        for bd in lay["buildings"]:
            tx, ty = bd["tile"]
            Fm = H @ np.array([[1.0 / S, 0, tx - win_t / 2], [0, 1.0 / S, ty - win_t / 2], [0, 0, 1]])
            ps.append(cv2.warpPerspective(frame, np.linalg.inv(Fm), (W, W), flags=cv2.INTER_LINEAR,
                                          borderMode=cv2.BORDER_REPLICATE))
            ys.append(bd["type"]); bs.append(b)
    return ps, np.array(ys), np.array(bs)


def _conv_block(i, o):
    return nn.Sequential(
        nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(True),
        nn.Conv2d(o, o, 3, padding=1), nn.BatchNorm2d(o))


class ResNet(nn.Module):
    def __init__(self, ncls, width=32):
        super().__init__()
        self.b1 = nn.Sequential(
            nn.Conv2d(3, width, 3, padding=1), nn.BatchNorm2d(width), nn.ReLU(True),
            nn.Conv2d(width, width, 3, padding=1), nn.BatchNorm2d(width), nn.ReLU(True),
            nn.MaxPool2d(2))
        self.b2 = _conv_block(width, width * 2)
        self.b3 = _conv_block(width * 2, width * 4)
        self.b4 = _conv_block(width * 4, width * 4)  # 残差块：输入输出同维
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.head = nn.Sequential(nn.Flatten(), nn.Dropout(0.3), nn.Linear(width * 4, ncls))

    def forward(self, x):
        x = self.b1(x)
        x = F.max_pool2d(F.relu(self.b2(x)), 2)
        x = F.max_pool2d(F.relu(self.b3(x)), 2)
        x = F.max_pool2d(F.relu(self.b4(x) + x), 2)
        return self.head(self.pool(x))


def aug(img, rng):
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), rng.uniform(-12, 12), rng.uniform(0.82, 1.20))
    M[0, 2] += rng.uniform(-14, 14); M[1, 2] += rng.uniform(-14, 14)
    g = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    if rng.random() < 0.8:
        g = np.clip(g.astype(np.float32) * rng.uniform(0.80, 1.22) + rng.uniform(-16, 16), 0, 255).astype(np.uint8)
    if rng.random() < 0.35:  # gamma
        ga = rng.uniform(0.7, 1.4)
        g = np.clip(((g / 255.0) ** ga) * 255.0, 0, 255).astype(np.uint8)
    if rng.random() < 0.35:  # hue/sat
        hsv = cv2.cvtColor(g, cv2.COLOR_BGR2HSV)
        hsv[..., 0] = (hsv[..., 0].astype(np.int16) + rng.randint(-12, 12)) % 180
        hsv[..., 1] = np.clip(hsv[..., 1].astype(np.float32) * rng.uniform(0.82, 1.18), 0, 255)
        g = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    if rng.random() < 0.3:  # cutout
        cs = rng.randint(6, 16); x0 = rng.randint(0, w - cs); y0 = rng.randint(0, h - cs)
        g[y0:y0 + cs, x0:x0 + cs] = 0
    return cv2.resize(g, (SIZE, SIZE), interpolation=cv2.INTER_AREA)


def tta_views(img):
    views = [img]
    M = cv2.getRotationMatrix2D((img.shape[1] / 2, img.shape[0] / 2), 6.0, 1.06)
    views.append(cv2.warpAffine(img, M, (img.shape[1], img.shape[0]), flags=cv2.INTER_LINEAR,
                                borderMode=cv2.BORDER_REPLICATE))
    M2 = cv2.getRotationMatrix2D((img.shape[1] / 2, img.shape[0] / 2), -6.0, 0.95)
    views.append(cv2.warpAffine(img, M2, (img.shape[1], img.shape[0]), flags=cv2.INTER_LINEAR,
                                borderMode=cv2.BORDER_REPLICATE))
    return views


def tensor(imgs):
    arr = [cv2.resize(g, (SIZE, SIZE), interpolation=cv2.INTER_AREA)[..., ::-1].astype(np.float32) / 255.0 for g in imgs]
    return torch.from_numpy(np.ascontiguousarray(np.stack(arr).transpose(0, 3, 1, 2)))


def train_predict(Xtr, ytr, Xte, ncls, epochs=140, seed=0, weights=None):
    seed = int(seed); rng = random.Random(seed); torch.manual_seed(seed)
    net = ResNet(ncls)
    opt = torch.optim.AdamW(net.parameters(), lr=2.5e-3, weight_decay=1e-3)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    yt = torch.from_numpy(np.asarray(ytr, np.int64))
    w = None if weights is None else torch.from_numpy(np.asarray(weights, np.float32))
    n, bs = len(Xtr), 24
    for ep in range(epochs):
        net.train()
        idx = list(range(n)); rng.shuffle(idx)
        for s in range(0, n, bs):
            sel = idx[s:s + bs]
            xb = tensor([aug(Xtr[i], rng) for i in sel])
            opt.zero_grad()
            F.cross_entropy(net(xb), yt[sel], label_smoothing=0.1,
                            weight=w).backward()
            opt.step()
        sched.step()
    net.eval()
    probs = []
    with torch.no_grad():
        for v in range(3):  # TTA
            views = [tta_views(x)[v] for x in Xte]
            probs.append(F.softmax(net(tensor(views)), 1).numpy())
    return np.argmax(sum(probs), axis=1)


def strat_folds(y, k=5, seed=7):
    rng = np.random.default_rng(seed); folds = np.zeros(len(y), int)
    for t in sorted(set(y)):
        idx = np.where(y == t)[0]; rng.shuffle(idx); folds[idx] = np.arange(len(idx)) % k
    return folds


def main():
    win_t = float(sys.argv[1]) if len(sys.argv) > 1 else 4.5
    seeds = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    epochs = int(sys.argv[3]) if len(sys.argv) > 3 else 140
    ps, y, bs = build(win_t)
    classes = sorted(set(y)); cmap = {c: i for i, c in enumerate(classes)}
    yi = np.array([cmap[t] for t in y])
    cnt = np.bincount(yi, minlength=len(classes))
    cw = (1.0 / np.sqrt(np.maximum(cnt, 1))); cw = cw / cw.mean()
    print("n=%d classes=%d win_t=%.1f seeds=%d epochs=%d majority=%.3f" % (
        len(y), len(classes), win_t, seeds, epochs, cnt.max() / len(y)), flush=True)
    folds = strat_folds(y)
    within_list, lobo_list = [], []
    for seed in range(seeds):
        yp = np.array([-1] * len(y))
        for f in sorted(set(folds)):
            te = folds == f; tr = ~te
            yp[te] = train_predict([ps[i] for i in np.where(tr)[0]], yi[tr],
                                   [ps[i] for i in np.where(te)[0]], len(classes), epochs, 100 + f + seed * 7, cw)
        within_list.append(float((yp == yi).mean()))
        print("  seed %d within=%.3f" % (seed, within_list[-1]), flush=True)
        yt2, yp2 = [], []
        for b in BASES:
            te = bs == b; tr = ~te
            keep = np.array([t in set(y[tr]) for t in y[te]])
            pr = train_predict([ps[i] for i in np.where(tr)[0]], yi[tr],
                               [ps[i] for i in np.where(te)[0]], len(classes), epochs, 7 + seed, cw)
            yt2 += list(yi[te][keep]); yp2 += list(pr[keep])
        lobo_list.append(float((np.array(yt2) == np.array(yp2)).mean()))
        print("  seed %d lobo=%.3f (n=%d)" % (seed, lobo_list[-1], len(yt2)), flush=True)
    res = {"n": int(len(y)), "classes": len(classes), "win_t": win_t, "epochs": epochs,
           "within_mean": float(np.mean(within_list)), "within_all": within_list,
           "lobo_mean": float(np.mean(lobo_list)), "lobo_all": lobo_list,
           "majority": float(cnt.max() / len(y))}
    json.dump(res, open(os.path.join(OUT, "cnn_lobo2_result_%.1f.json" % win_t), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False), flush=True)


main()
