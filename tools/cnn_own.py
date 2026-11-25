# -*- coding: utf-8 -*-
"""步骤 5：用「自家村庄」easyocr 自动标注样本重训 CNN，并做跨域测试。

数据：
  A) 自家村庄：out/overlay/_auto_label/sweep3/g3_<x>_<y>.png（220×220，中心裁 108 后与战场正视图同尺度 ~4.7 格）
     标签来自 g3_labels.json（easyocr 名称卡片/面板标题模糊匹配，含置信比 ratio）
  B) 战场：107 栋 H 反投影正视图（既有标签，24px/格）
评估：
  1) 自家村庄 分组 CV（按 4×4 区域分折，避免相邻重叠泄漏）
  2) 战场 107 栋 → 自家村庄（跨域泛化）
  3) 混合训练 → 各自测试
"""
import json, os, math, random
import numpy as np, cv2
import torch, torch.nn as nn, torch.nn.functional as F

BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
AUTO = os.path.join(BASE, "out", "overlay", "_auto_label")
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


def train(Xtr, ytr, ncls, epochs, seed):
    seed = int(seed); rng = random.Random(seed); torch.manual_seed(seed)
    net = Net(ncls)
    opt = torch.optim.AdamW(net.parameters(), lr=3e-3, weight_decay=2e-3)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    yt = torch.from_numpy(np.array(ytr, np.int64))
    n, bs = len(Xtr), 24
    for ep in range(epochs):
        net.train(); idx = list(range(n)); rng.shuffle(idx)
        for s in range(0, n, bs):
            sel = idx[s:s + bs]
            xb = to_tensor([aug(Xtr[i], rng) for i in sel])
            opt.zero_grad(); F.cross_entropy(net(xb), yt[sel], label_smoothing=0.05).backward(); opt.step()
        sched.step()
    net.eval()
    return net


@torch.no_grad()
def predict(net, imgs, bs=64):
    out = []
    for i in range(0, len(imgs), bs):
        out.append(F.softmax(net(to_tensor(imgs[i:i + bs])), 1).numpy())
    return np.concatenate(out, 0)


DEF = {"air-defense", "air-sweeper", "archer-tower", "bomb-tower", "cannon", "eagle-artillery",
       "firespitter", "hidden-tesla", "inferno-tower", "monolith", "mortar", "multi-archer-tower",
       "scattershot", "spell-tower", "town-hall", "wizard-tower", "x-bow", "clan-castle",
       "ricochet-cannon", "wall"}


def load_own(min_ratio=0.6):
    lab_path = os.path.join(AUTO, "g3_labels.json")
    labels = json.load(open(lab_path, encoding="utf-8"))
    crops, ys, groups = [], [], []
    for r in labels:
        if not r.get("name") or r.get("ratio", 0) < min_ratio:
            continue
        t = r.get("type")
        if t not in DEF:
            continue
        p = os.path.join(AUTO, "sweep3", "g3_%d_%d.png" % (r["x"], r["y"]))
        if not os.path.exists(p):
            continue
        img = imread(p)
        h = img.shape[0] // 2
        c = img[h - 54:h + 54, img.shape[1] // 2 - 54:img.shape[1] // 2 + 54]
        if c.shape[0] != 108 or c.shape[1] != 108:
            continue
        crops.append(c); ys.append(t)
        groups.append((r["x"] // 200, r["y"] // 200))
    return crops, np.array(ys), groups


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
            p = cv2.warpPerspective(frame, np.linalg.inv(Fm), (W, W), flags=cv2.INTER_LINEAR,
                                    borderMode=cv2.BORDER_REPLICATE)
            crops.append(cv2.resize(p, (108, 108), interpolation=cv2.INTER_AREA))
            ys.append(bd["type"])
    return crops, np.array(ys)


def geo_cv(X, y, groups, ncls, classes, folds=3, epochs=60, seed=0):
    accs = []
    gl = sorted(set(groups))
    rng = random.Random(seed); rng.shuffle(gl)
    assign = {g: i % folds for i, g in enumerate(gl)}
    yp = np.array([-1] * len(y))
    for f in range(folds):
        te = np.array([assign[g] == f for g in groups]); tr = ~te
        if te.sum() == 0 or tr.sum() == 0:
            continue
        net = train([X[i] for i in np.where(tr)[0]], [classes.index(y[i]) for i in np.where(tr)[0]],
                    ncls, epochs, seed + f)
        prob = predict(net, [X[i] for i in np.where(te)[0]])
        yp[te] = [classes[int(np.argmax(p))] for p in prob]
    ok = yp != -1
    return float((yp[ok] == y[ok]).mean()) if ok.sum() else float("nan")


def cross_train_test(Xtr, ytr, Xte, yte, epochs=80, seed=0):
    classes = sorted(set(list(ytr) + list(yte)))
    net = train(Xtr, [classes.index(t) for t in ytr], len(classes), epochs, seed)
    prob = predict(net, Xte)
    pred = [classes[int(np.argmax(p))] for p in prob]
    known = np.array([t in set(ytr) for t in yte])
    acc_all = float(np.mean([pred[i] == yte[i] for i in range(len(yte))]))
    acc_known = float(np.mean([pred[i] == yte[i] for i in np.where(known)[0]])) if known.sum() else float("nan")
    return acc_all, acc_known, int(known.sum()), len(yte)


def main():
    own, yo, go = load_own()
    bat, yb = load_battle()
    print("own=%d battle=%d" % (len(own), len(bat)))
    print("own classes:", {c: int((yo == c).sum()) for c in sorted(set(yo))})
    res = {"own_n": len(own), "battle_n": len(bat),
           "own_classes": {c: int((yo == c).sum()) for c in sorted(set(yo))}}
    if len(own) >= 30:
        cls = sorted(set(yo))
        res["own_grouped_cv"] = geo_cv(own, yo, go, len(cls), cls, folds=3, epochs=60, seed=1)
        print("own grouped CV acc = %.3f" % res["own_grouped_cv"])
    if len(own) >= 10:
        a, ak, nk, nt = cross_train_test(bat, yb, own, yo, epochs=80, seed=2)
        res.update({"battle_to_own_all": a, "battle_to_own_known": ak, "known_n": nk, "own_total": nt})
        print("battle->own acc_all=%.3f acc_known=%.3f (known %d/%d)" % (a, ak, nk, nt))
        a2, ak2, nk2, nt2 = cross_train_test(own, yo, bat, yb, epochs=80, seed=3)
        res.update({"own_to_battle_all": a2, "own_to_battle_known": ak2})
        print("own->battle acc_all=%.3f acc_known=%.3f" % (a2, ak2))
    json.dump(res, open(os.path.join(REC, "cnn_own_result.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("-> cnn_own_result.json")


main()
