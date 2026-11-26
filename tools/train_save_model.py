# -*- coding: utf-8 -*-
"""训练 27px 识别小 CNN，并产出可复现的可行性证据。

产物（默认 models/）：
- recog_27px.pt         state_dict + classes + input_size（供 clashlab.recog_model 推理）
- metrics.json          within-5fold / leave-one-base-out 真实指标 + 混淆矩阵
- confusion_within5.png / confusion_lobo.png

协议（与 docs/RECOG_RESULTS.md 同一口径）：
- within-5fold：全体样本按类别分层 5 折，out-of-fold 统计
- leave-one-base-out：每次留一整阵，只统计「该类在训练集出现过」的测试样本

网络与增强直接复用 tools/train_from_annotations.py 的定义（同一 Net、同一 aug），
为了在 CPU 上守住 5 分钟预算，训练循环用 channels_last + bf16 autocast 加速，
默认 50 epochs（参考跑为 60 epochs fp32，见 --epochs / --precision）。

数据：clashlab.recog_dataset.build_dataset，支持 out/annotate/*_annotated.json
（人工校正坐标，优先）与 bases/th16/*/layout.json（原始 layout，回退）。

用法：
    python tools/train_save_model.py                    # auto：有标注用标注，否则用 layout
    python tools/train_save_model.py --source layout     # 强制用原始 layout 对照
    python tools/train_save_model.py --epochs 60 --precision fp32   # 高质量档（>5 分钟）
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import random
import sys
import time
from datetime import datetime, timezone

import cv2
import numpy as np
import torch
import torch.nn.functional as F

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from clashlab.recog_dataset import build_dataset  # noqa: E402
from clashlab.recog_model import ARCH, INPUT_SIZE, Net, save_model  # noqa: E402

DEFAULT_LAYOUTS = ["out/annotate/*_annotated.json", "bases/th16/*/layout.json"]
REFERENCE = {"within_5fold": 0.734, "lobo": 0.641, "source": "docs/RECOG_RESULTS.md",
             "note": "参考跑：24/48/96 + 60 epochs + fp32；本脚本默认配置的对照见 docs/ML_FEASIBILITY.md"}


def aug(img, rng):
    """与 tools/train_from_annotations.py 完全一致的增强：旋转/缩放/平移/亮度/擦除。"""
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), rng.uniform(-8, 8), rng.uniform(0.9, 1.1))
    M[0, 2] += rng.uniform(-8, 8)
    M[1, 2] += rng.uniform(-8, 8)
    g = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    if rng.random() < 0.7:
        g = np.clip(g.astype(np.float32) * rng.uniform(0.88, 1.12) + rng.uniform(-10, 10), 0, 255).astype(np.uint8)
    if rng.random() < 0.2:
        cs = rng.randint(8, 18)
        x0 = rng.randint(0, w - cs)
        y0 = rng.randint(0, h - cs)
        g[y0:y0 + cs, x0:x0 + cs] = 0
    return g


def tensor(imgs):
    """BGR uint8 list → RGB float32 NCHW ∈ [0,1]（与 recog_model 预处理严格一致）。"""
    arr = [g[..., ::-1].astype(np.float32) / 255.0 for g in imgs]
    return torch.from_numpy(np.ascontiguousarray(np.stack(arr).transpose(0, 3, 1, 2)))


def _maybe_cl(x, channels_last):
    return x.to(memory_format=torch.channels_last) if channels_last else x


def _loss(net, xb, yb, weight, precision):
    if precision == "bf16":
        with torch.autocast("cpu", dtype=torch.bfloat16):
            return F.cross_entropy(net(xb), yb, label_smoothing=0.05, weight=weight)
    return F.cross_entropy(net(xb), yb, label_smoothing=0.05, weight=weight)


def fit(crops_tr, y_tr, ncls, epochs, seed, weight, bs=24, channels_last=True, precision="bf16"):
    """训练一个模型（返回 eval 模式的 net）。同 seed 下训练过程可复现。"""
    rng = random.Random(seed)
    torch.manual_seed(seed)
    net = Net(ncls)
    if channels_last:
        net = net.to(memory_format=torch.channels_last)
    opt = torch.optim.AdamW(net.parameters(), lr=3e-3, weight_decay=2e-3)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=max(epochs, 1))
    yt = torch.from_numpy(np.asarray(y_tr, np.int64))
    n = len(crops_tr)
    for _ in range(epochs):
        net.train()
        idx = list(range(n))
        rng.shuffle(idx)
        for s in range(0, n, bs):
            sel = idx[s:s + bs]
            xb = _maybe_cl(tensor([aug(crops_tr[i], rng) for i in sel]), channels_last)
            opt.zero_grad()
            _loss(net, xb, yt[sel], weight, precision).backward()
            opt.step()
        sched.step()
    net.eval()
    return net


def predict(net, crops, channels_last=True):
    with torch.no_grad():
        xb = _maybe_cl(tensor(crops), channels_last)
        return net(xb).argmax(1).numpy()


def train_predict(crops_tr, y_tr, crops_te, ncls, epochs, seed, weight,
                  bs=24, channels_last=True, precision="bf16"):
    net = fit(crops_tr, y_tr, ncls, epochs, seed, weight, bs, channels_last, precision)
    return predict(net, crops_te, channels_last)


def strat_folds(y, k=5, seed=7):
    rng = np.random.default_rng(seed)
    folds = np.zeros(len(y), int)
    for t in sorted(set(y.tolist())):
        idx = np.where(y == t)[0]
        rng.shuffle(idx)
        folds[idx] = np.arange(len(idx)) % k
    return folds


def confusion(y_true, y_pred, ncls):
    m = np.zeros((ncls, ncls), np.int64)
    for t, p in zip(y_true, y_pred):
        m[int(t), int(p)] += 1
    return m.tolist()


def draw_confusion(matrix, classes, title, path):
    """用 OpenCV 画混淆矩阵（不引入 matplotlib）：行=真值，列=预测，格内写计数。"""
    m = np.asarray(matrix, np.int64)
    n = len(classes)
    cell, left, top, pad = 52, 150, 70, 12
    w = left + n * cell + pad
    h = top + n * cell + 70 + pad
    img = np.full((h, w, 3), 255, np.uint8)
    row_sum = np.maximum(m.sum(axis=1, keepdims=True), 1)
    norm = m / row_sum
    for i in range(n):
        for j in range(n):
            v = float(norm[i, j])
            color = (int(255 - 200 * v), int(255 - 120 * v), int(255 - 20 * v))
            x0, y0 = left + j * cell, top + i * cell
            cv2.rectangle(img, (x0, y0), (x0 + cell - 2, y0 + cell - 2), color, -1)
            if m[i, j]:
                cv2.putText(img, str(int(m[i, j])), (x0 + 6, y0 + 32),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (20, 20, 20), 1, cv2.LINE_AA)
    for i, c in enumerate(classes):
        cv2.putText(img, c[:20], (4, top + i * cell + 32), cv2.FONT_HERSHEY_SIMPLEX, 0.42,
                    (30, 30, 30), 1, cv2.LINE_AA)
        cv2.putText(img, str(i), (left + i * cell + 18, top - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                    (30, 30, 30), 1, cv2.LINE_AA)
    cv2.putText(img, title, (4, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.putText(img, "rows=true (name,index)  cols=pred(index)", (4, top + n * cell + 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.48, (90, 90, 90), 1, cv2.LINE_AA)
    ok, buf = cv2.imencode(".png", img)
    if not ok:
        raise RuntimeError("混淆矩阵编码失败：%s" % path)
    buf.tofile(path)  # cv2.imwrite 在非 ASCII 路径下会静默失败
    return path


def resolve_files(source, layouts):
    pats = layouts if layouts else DEFAULT_LAYOUTS
    ann, lay = [], []
    for pat in pats:
        for p in sorted(glob.glob(pat)):
            if os.path.basename(p).endswith("_annotated.json"):
                ann.append(p)
            elif os.path.basename(p) == "layout.json":
                lay.append(p)
    if source == "layout":
        return lay, "layout"
    if source == "annotate":
        return ann, "annotate"
    return (ann, "annotate") if ann else (lay, "layout")


def main():
    ap = argparse.ArgumentParser(description="训练 27px CNN 并保存 checkpoint/metrics/confusion")
    ap.add_argument("--layouts", nargs="+", default=None,
                    help="数据 glob；默认 auto（标注优先，回退 layout）")
    ap.add_argument("--source", choices=["auto", "annotate", "layout"], default="auto")
    ap.add_argument("--epochs", type=int, default=40,
                    help="默认 40（实测 <4 分钟，5 分钟预算内）；参考跑为 60")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--precision", choices=["bf16", "fp32"], default="bf16")
    ap.add_argument("--no-channels-last", action="store_true")
    ap.add_argument("--models-dir", default=os.path.join(ROOT, "models"))
    ap.add_argument("--checkpoint", default="recog_27px.pt")
    ap.add_argument("--threads", type=int, default=0)
    ap.add_argument("--only-defense", action="store_true",
                    help="只用防御类样本（assets.STATS + TH16_OVERRIDE），去掉经济/兵营/陷阱")
    a = ap.parse_args()

    torch.set_num_threads(a.threads or min(os.cpu_count() or 4, 8))
    cl = not a.no_channels_last
    t_start = time.time()
    files, source = resolve_files(a.source, a.layouts)
    if not files:
        raise SystemExit("没有可用标注/layout 文件（检查 out/annotate/*.json 或 bases/th16/*/layout.json）")
    crops, labels, bases = build_dataset(files)
    if not crops:
        raise SystemExit("build_dataset 返回空（layout 缺 quad 或 base.png 缺失）")
    if a.only_defense:
        from clashlab import assets as _assets
        keep = set(_assets.STATS) | set(getattr(_assets, "TH16_OVERRIDE", {}))
        idx = [i for i, lb in enumerate(labels) if lb in keep]
        dropped = len(labels) - len(idx)
        crops = [crops[i] for i in idx]
        labels = [labels[i] for i in idx]
        bases = [bases[i] for i in idx]
        print("[filter] only-defense keep=%d dropped=%d" % (len(idx), dropped), flush=True)

    classes = sorted(set(labels))
    cmap = {c: i for i, c in enumerate(classes)}
    y = np.array([cmap[t] for t in labels], np.int64)
    bsArr = np.array(bases)
    ncls = len(classes)
    cnt = np.bincount(y, minlength=ncls)
    w = torch.from_numpy((1.0 / np.sqrt(np.maximum(cnt, 1))).astype(np.float32))
    w = (w / w.mean()).float()
    t_data = time.time() - t_start
    print("[data] source=%s files=%d n=%d bases=%d classes=%d majority=%.3f load_s=%.2f" % (
        source, len(files), len(y), len(set(bases)), ncls, cnt.max() / len(y), t_data), flush=True)
    print("[train] epochs=%d precision=%s channels_last=%s threads=%d" % (
        a.epochs, a.precision, cl, torch.get_num_threads()), flush=True)

    kw = dict(channels_last=cl, precision=a.precision)
    # ---- within-5fold ----
    t0 = time.time()
    folds = strat_folds(y, 5, seed=a.seed)
    yp = np.full(len(y), -1, np.int64)
    per_fold = []
    for f in sorted(set(folds.tolist())):
        te = folds == f
        tr = ~te
        pr = train_predict([crops[i] for i in np.where(tr)[0]], y[tr],
                           [crops[i] for i in np.where(te)[0]], ncls, a.epochs,
                           a.seed + int(f), w, **kw)
        yp[te] = pr
        per_fold.append(float((pr == y[te]).mean()))
        print("  [within] fold %d acc=%.3f (n=%d)" % (f, per_fold[-1], int(te.sum())), flush=True)
    within_acc = float((yp == y).mean())
    within_cm = confusion(y, yp, ncls)
    t_within = time.time() - t0
    print("[within] acc=%.3f n=%d s=%.1f" % (within_acc, len(y), t_within), flush=True)

    # ---- leave-one-base-out ----
    t0 = time.time()
    lobo_true, lobo_pred, per_base, excluded = [], [], {}, 0
    for b in sorted(set(bases)):
        te = bsArr == b
        tr = ~te
        seen = set(y[tr].tolist())
        keep = np.array([int(v) in seen for v in y[te]])
        excluded += int((~keep).sum())
        pr = train_predict([crops[i] for i in np.where(tr)[0]], y[tr],
                           [crops[i] for i in np.where(te)[0]], ncls, a.epochs,
                           a.seed + 100, w, **kw)
        yt_b, yp_b = y[te][keep], pr[keep]
        lobo_true += yt_b.tolist()
        lobo_pred += yp_b.tolist()
        per_base[b] = {"acc": float((yt_b == yp_b).mean()) if len(yt_b) else None,
                       "n": int(len(yt_b)), "excluded": int((~keep).sum())}
        print("  [lobo] base %s acc=%.3f n=%d excluded=%d" % (
            b, per_base[b]["acc"] or 0.0, len(yt_b), int((~keep).sum())), flush=True)
    lobo_acc = float((np.array(lobo_true) == np.array(lobo_pred)).mean())
    lobo_cm = confusion(lobo_true, lobo_pred, ncls)
    t_lobo = time.time() - t0
    print("[lobo] acc=%.3f n=%d s=%.1f" % (lobo_acc, len(lobo_true), t_lobo), flush=True)

    # ---- 全量训练 → 推理用 checkpoint ----
    t0 = time.time()
    net = fit(crops, y, ncls, a.epochs, a.seed, w, **kw)
    t_final = time.time() - t0
    elapsed = time.time() - t_start

    os.makedirs(a.models_dir, exist_ok=True)
    ckpt_path = os.path.join(a.models_dir, a.checkpoint)
    save_model(net, classes, ckpt_path, input_size=INPUT_SIZE,
               grid=44, win_t=4.5, data_source=source, n_samples=len(y),
               trained_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
               within_5fold=within_acc, lobo=lobo_acc)
    fig_within = os.path.join(a.models_dir, "confusion_within5.png")
    fig_lobo = os.path.join(a.models_dir, "confusion_lobo.png")
    draw_confusion(within_cm, classes, "within-5fold OOF (acc=%.3f)" % within_acc, fig_within)
    draw_confusion(lobo_cm, classes, "leave-one-base-out (acc=%.3f)" % lobo_acc, fig_lobo)

    metrics = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "checkpoint": os.path.relpath(ckpt_path, ROOT).replace(os.sep, "/"),
        "arch": ARCH,
        "input_size": INPUT_SIZE,
        "classes": classes,
        "data": {
            "source": source,
            "files": [os.path.relpath(p, ROOT).replace(os.sep, "/") for p in files],
            "n_samples": int(len(y)),
            "n_bases": int(len(set(bases))),
            "n_classes": int(ncls),
            "per_base": {b: int((bsArr == b).sum()) for b in sorted(set(bases))},
            "per_class": {c: int(cnt[i]) for i, c in enumerate(classes)},
            "build_s": round(t_data, 2),
        },
        "train": {
            "epochs": a.epochs,
            "seed": a.seed,
            "batch_size": 24,
            "precision": a.precision,
            "channels_last": bool(cl),
            "threads": torch.get_num_threads(),
            "optimizer": "AdamW lr=3e-3 wd=2e-3 + cosine",
            "loss": "cross_entropy(label_smoothing=0.05, class_weight=1/sqrt(count))",
            "augmentation": "rotate±8° scale0.9-1.1 shift±8px brightness/contrast p=0.7 cutout p=0.2",
            "torch": torch.__version__,
        },
        "protocol": {
            "within_5fold": "全体样本按类别分层 5 折（seed=%d），out-of-fold 统计" % a.seed,
            "lobo": "每次留一整阵训练其余阵；只统计训练集中出现过的类别（与旧口径一致）",
        },
        "within_5fold": {
            "accuracy": within_acc,
            "n": int(len(y)),
            "per_fold": per_fold,
            "majority_baseline": float(cnt.max() / len(y)),
            "confusion": within_cm,
            "seconds": round(t_within, 1),
        },
        "lobo": {
            "accuracy": lobo_acc,
            "n": int(len(lobo_true)),
            "excluded_unseen_class": int(excluded),
            "per_base": per_base,
            "majority_baseline": float(cnt.max() / len(y)),
            "confusion": lobo_cm,
            "seconds": round(t_lobo, 1),
        },
        "runtime": {"total_s": round(elapsed, 1), "final_fit_s": round(t_final, 1),
                    "cpu_only": True},
        "figures": {
            "within_5fold": os.path.relpath(fig_within, ROOT).replace(os.sep, "/"),
            "lobo": os.path.relpath(fig_lobo, ROOT).replace(os.sep, "/"),
        },
        "reference": REFERENCE,
    }
    metrics_path = os.path.join(a.models_dir, "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, ensure_ascii=False, indent=1)

    print("[save] %s" % ckpt_path, flush=True)
    print("[save] %s" % metrics_path, flush=True)
    print("[time] total=%.1fs within=%.1fs lobo=%.1fs final=%.1fs" % (
        elapsed, t_within, t_lobo, t_final), flush=True)
    print(json.dumps({"within_5fold": within_acc, "lobo": lobo_acc,
                      "n": int(len(y)), "classes": ncls, "runtime_s": round(elapsed, 1)},
                     ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
