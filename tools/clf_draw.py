# -*- coding: utf-8 -*-
# clf_draw.py — 测试块预测框标注 + 混淆矩阵图（复用 train_clf 特征）
import os, sys, csv, cv2, numpy as np, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import train_clf as TC

ROOT = TC.ROOT
# 重建训练/测试特征
Xtr, ytr, _ = TC.build_set(TC.train)
mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-6
Xtr_n = (Xtr - mu) / sd

def nearest(q):
    d = np.linalg.norm(Xtr_n - q, axis=1)
    i = int(np.argmin(d))
    return ytr[i], float(d[i])

rows_out = []
ann = {}
for r in TC.test:
    blk = TC.get_block(r["block"])
    f = TC.feat_on(blk, int(r["cx"]), int(r["cy"]), r["footprint"])
    fn = (f - mu) / sd
    pred, d = nearest(fn)
    conf = 1.0 / (1.0 + d)
    rows_out.append({"block": r["block"], "gt": r["class"], "pred": pred,
                     "conf": round(conf, 3), "gt_cx": int(r["cx"]), "gt_cy": int(r["cy"])})
    ann.setdefault(r["block"], []).append((r, pred, conf))

# --- 标注图：b10 / b14 并排 ---
panels = []
for b in ["b10", "b14"]:
    im = TC.get_block(b).copy()
    for r, pred, conf in ann[b]:
        cx, cy = int(r["cx"]), int(r["cy"])
        cv2.rectangle(im, (cx-112, cy-112), (cx+112, cy+112), (0, 200, 0), 2)
        txt = f"pred:{pred} conf={conf:.2f} gt:{r['class']}"
        cv2.putText(im, txt, (cx-110, cy-120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)
    panels.append(cv2.resize(im, (712, 412)))
out = np.hstack(panels)
ok, buf = cv2.imencode(".png", out)
buf.tofile(os.path.join(ROOT, "out", "overlay", "recog_clf_l2.png"))
print("saved recog_clf_l2.png")

# --- 混淆矩阵（测试集3例） ---
gt_classes = sorted(set(r["gt"] for r in rows_out))
pred_classes = sorted(set(r["pred"] for r in rows_out))
cm = collections.Counter((r["gt"], r["pred"]) for r in rows_out)
cell = 90
cols = len(pred_classes) + 1
rows = len(gt_classes) + 1
canvas = np.full((rows*cell, cols*cell, 3), 255, np.uint8)
# 表头
for j, p in enumerate(pred_classes):
    cv2.putText(canvas, p, ((j+1)*cell+8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0,0,0), 1)
for i, g in enumerate(gt_classes):
    cv2.putText(canvas, g, (8, (i+1)*cell+30), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0,0,0), 1)
for i, g in enumerate(gt_classes):
    for j, p in enumerate(pred_classes):
        n = cm.get((g, p), 0)
        if n:
            color = (0, 180, 0) if g == p else (0, 0, 220)
            cv2.rectangle(canvas, ((j+1)*cell+5, (i+1)*cell+5), ((j+2)*cell-5, (i+2)*cell-5), color, -1)
            cv2.putText(canvas, str(n), ((j+1)*cell+35, (i+1)*cell+55), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255,255,255), 2)
cv2.putText(canvas, "rows=GT cols=PRED (test set 3 cases)", (10, rows*cell-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1)
ok, buf = cv2.imencode(".png", canvas)
buf.tofile(os.path.join(ROOT, "out", "overlay", "clf_confusion.png"))
print("saved clf_confusion.png")
for r in rows_out:
    print(r)
