# -*- coding: utf-8 -*-
"""训练四角回归模型（预加载 + 小尺寸增强，CPU 2 分钟内）。

    python tools/train_quad_model.py --epochs 120
产物：models/quad_model.pt、models/quad_metrics.json
"""
import argparse, json, math, os, random, sys
import numpy as np
import cv2
import torch
import torch.nn as nn

BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab.quad_model import QuadNet, INPUT_W, INPUT_H  # noqa: E402

MANIFEST = os.path.join(BASE, "out", "quad_dataset", "manifest.json")


def load_split():
    rows = json.load(open(MANIFEST, encoding="utf-8"))["rows"]
    out = []
    for r in rows:
        img = cv2.imdecode(np.fromfile(r["image"], np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            continue
        rgb = cv2.cvtColor(cv2.resize(img, (INPUT_W, INPUT_H), interpolation=cv2.INTER_AREA),
                           cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        x = np.transpose(rgb, (2, 0, 1))
        w, h = img.shape[1], img.shape[0]
        y = np.array([[p[0] / w, p[1] / h] for p in r["quad"]], np.float32).reshape(-1)
        out.append((x, y, r["split"]))
    return out


def aug(x, y, rng):
    """在 320×180 输入上做旋转/缩放/平移，同步变换归一化四角。"""
    img = (np.transpose(x, (1, 2, 0)) * 255).astype(np.uint8)
    ang = rng.uniform(-5, 5)
    scale = rng.uniform(0.9, 1.1)
    M = cv2.getRotationMatrix2D((INPUT_W / 2, INPUT_H / 2), ang, scale)
    M[0, 2] += rng.uniform(-8, 8); M[1, 2] += rng.uniform(-8, 8)
    img2 = cv2.warpAffine(img, M, (INPUT_W, INPUT_H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    pts = np.array([[y[i] * INPUT_W, y[i + 1] * INPUT_H] for i in range(0, 8, 2)], np.float32)
    pts2 = cv2.transform(np.array([pts]), M)[0]
    y2 = np.stack([pts2[:, 0] / INPUT_W, pts2[:, 1] / INPUT_H], axis=1).reshape(-1)
    x2 = np.transpose(img2.astype(np.float32) / 255.0, (2, 0, 1))
    return x2, y2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=120)
    ap.add_argument("--bs", type=int, default=8)
    ap.add_argument("--out", default=os.path.join(BASE, "models"))
    a = ap.parse_args()
    data = load_split()
    train = [d for d in data if d[2] == "train"]
    val = [d for d in data if d[2] == "val"] or train[-2:]
    print("[data] train=%d val=%d input=%dx%d" % (len(train), len(val), INPUT_W, INPUT_H), flush=True)
    net = QuadNet()
    opt = torch.optim.AdamW(net.parameters(), lr=1.2e-3, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=a.epochs)
    rng = random.Random(7)
    for ep in range(a.epochs):
        net.train()
        idx = list(range(len(train))); rng.shuffle(idx)
        total, n = 0.0, 0
        for s in range(0, len(idx), a.bs):
            xs, ys = [], []
            for i in idx[s:s + a.bs]:
                x, y = aug(train[i][0], train[i][1], rng)
                xs.append(x); ys.append(y)
            xb = torch.from_numpy(np.stack(xs)).float()
            yb = torch.from_numpy(np.stack(ys)).float()
            opt.zero_grad()
            loss = nn.functional.smooth_l1_loss(net(xb), yb)
            loss.backward(); opt.step()
            total += float(loss); n += 1
        sched.step()
        if ep % 20 == 0 or ep == a.epochs - 1:
            print("[train] ep=%d loss=%.5f" % (ep, total / max(1, n)), flush=True)
    net.eval()
    errs_px, errs_tile = [], []
    with torch.no_grad():
        for x, y, _ in val:
            pred = net(torch.from_numpy(np.stack([x])).float())[0].numpy()
            pp = np.array([[pred[i] * INPUT_W, pred[i + 1] * INPUT_H] for i in range(0, 8, 2)])
            gp = np.array([[y[i] * INPUT_W, y[i + 1] * INPUT_H] for i in range(0, 8, 2)])
            e = float(np.mean(np.linalg.norm(pp - gp, axis=1)))
            errs_px.append(e)
            errs_tile.append(e / (math.hypot(INPUT_W, INPUT_H) / (44 * 1.414)))
    metrics = {"n_train": len(train), "n_val": len(val), "epochs": a.epochs,
               "corner_err_px_mean": round(float(np.mean(errs_px)), 2),
               "corner_err_px_max": round(float(np.max(errs_px)), 2),
               "corner_err_tile_mean": round(float(np.mean(errs_tile)), 3),
               "note": "伪标签来自草地边界检测；指标为对伪标签的拟合误差，非人工真值"}
    os.makedirs(a.out, exist_ok=True)
    torch.save({"state_dict": net.state_dict(), "input_size": (INPUT_W, INPUT_H), "metrics": metrics},
               os.path.join(a.out, "quad_model.pt"))
    json.dump(metrics, open(os.path.join(a.out, "quad_metrics.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("[metrics]", json.dumps(metrics, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
