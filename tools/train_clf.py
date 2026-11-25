# -*- coding: utf-8 -*-
# train_clf.py — 实景裁片监督分类：HOG+HSV+底面尺寸，手写kNN(k=1)，跨块划分
# 复跑: python tools/train_clf.py ；随机种子固定 20261124
import os, csv, cv2, numpy as np, json, collections

ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BLKDIR = os.path.join(ROOT, "out", "overlay", "blocks")
SEED = 20261124
rng = np.random.default_rng(SEED)
WIN = 224

# ---------- 特征 ----------
def hog_feat(gray):
    g = cv2.resize(gray, (64, 64), interpolation=cv2.INTER_AREA)
    gx = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
    mag = cv2.magnitude(gx, gy)
    ang = cv2.phase(gx, gy, angleInDegrees=True) % 180
    cell = 8
    nb = 9
    cells = []
    for i in range(0, 64, cell):
        for j in range(0, 64, cell):
            m = mag[i:i+cell, j:j+cell].ravel()
            a = ang[i:i+cell, j:j+cell].ravel()
            h = np.zeros(nb)
            if len(m):
                idx = (a / 20.0).astype(int) % nb
                np.add.at(h, idx, m)
            cells.append(h)
    cells = np.array(cells)  # (64,9)
    # 2x2 block L2 归一化（滑动步长1格）
    vecs = []
    for bi in range(0, 7, 1):
        for bj in range(0, 7, 1):
            block = np.concatenate([cells[bi*8+bj], cells[bi*8+bj+1],
                                    cells[(bi+1)*8+bj], cells[(bi+1)*8+bj+1]])
            n = np.linalg.norm(block) + 1e-6
            vecs.append(block / n)
    return np.concatenate(vecs)

def hsv_hist(bgr):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[:, :, 0].ravel(), hsv[:, :, 1].ravel(), hsv[:, :, 2].ravel()
    hh = np.histogram(h, bins=16, range=(0, 180))[0]
    sh = np.histogram(s, bins=8, range=(0, 256))[0]
    vh = np.histogram(v, bins=8, range=(0, 256))[0]
    out = np.concatenate([hh, sh, vh]).astype(float)
    return out / (out.sum() + 1e-6)

def footprint_feat(fp):
    w, h = fp.split("x")
    return np.array([int(w)/4.0, int(h)/4.0])

def feat_on(block, cx, cy, fp, scale=1.0):
    h, w = block.shape[:2]
    r = int(WIN/2*scale)
    cx, cy = int(round(cx)), int(round(cy))
    x0, y0 = max(0, cx-r), max(0, cy-r)
    x1, y1 = min(w, cx+r), min(h, cy+r)
    crop = block[y0:y1, x0:x1]
    if crop.size == 0:
        crop = np.zeros((WIN, WIN, 3), np.uint8)
    else:
        crop = cv2.resize(crop, (WIN, WIN), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    f = np.concatenate([hog_feat(gray), hsv_hist(crop), footprint_feat(fp)])
    return f

# ---------- 读标注 ----------
labels = []
with open(os.path.join(ROOT, "out", "recog", "labels_l2.csv"), encoding="utf-8") as f:
    for row in csv.DictReader(f):
        labels.append(row)
print(f"标注实例 {len(labels)} 栋")

blocks_img = {}
def get_block(b):
    if b not in blocks_img:
        blocks_img[b] = cv2.imdecode(np.fromfile(os.path.join(BLKDIR, b + ".png"), dtype=np.uint8), cv2.IMREAD_COLOR)
    return blocks_img[b]

# ---------- 跨块划分: A训练 b01,b05,b06,b09,b11,b12 ; B测试 b10,b14 ----------
TRAIN_BLKS = {"b01", "b05", "b06", "b09", "b11", "b12"}
TEST_BLKS = {"b10", "b14"}

train = [r for r in labels if r["block"] in TRAIN_BLKS]
test = [r for r in labels if r["block"] in TEST_BLKS]
print(f"训练 {len(train)} 例 / 测试 {len(test)} 例")

def build_set(rows, scale=1.0, block_override=None):
    X, y, meta = [], [], []
    for r in rows:
        blk = block_override(r) if block_override else get_block(r["block"])
        cx, cy = int(r["cx"])*scale, int(r["cy"])*scale
        X.append(feat_on(blk, cx, cy, r["footprint"], scale=scale))
        y.append(r["class"]); meta.append(r)
    return np.array(X), y, meta

Xtr, ytr, _ = build_set(train)
Xte, yte, mte = build_set(test)

# z-score（仅用训练）
mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-6
Xtr_n = (Xtr - mu) / sd
Xte_n = (Xte - mu) / sd

# ---------- 手写 kNN k=1 ----------
def knn_predict(Xq, Xref, yref, k=1):
    preds = []
    for q in Xq:
        d = np.linalg.norm(Xref - q, axis=1)
        nn = np.argsort(d)[:k]
        votes = collections.Counter([yref[i] for i in nn])
        preds.append(votes.most_common(1)[0][0])
    return preds

pred = knn_predict(Xte_n, Xtr_n, ytr, k=1)
print("测试预测:", list(zip([m['block']+':'+m['class'] for m in mte], pred)))

# ---------- 降采样 1/4 测试（20px/格） ----------
# 测试块整体缩到1/4，坐标同比例
def quarter_block(r):
    im = get_block(r["block"])
    return cv2.resize(im, (im.shape[1]//4, im.shape[0]//4), interpolation=cv2.INTER_AREA)

Xteq, yteq, mq = [], [], []
for r in test:
    im = quarter_block(r)
    cx, cy = int(int(r["cx"])*0.25), int(int(r["cy"])*0.25)
    Xteq.append(feat_on(im, cx, cy, r["footprint"], scale=1.0))
    yteq.append(r["class"]); mq.append(r)
Xteq = np.array(Xteq)
Xteq_n = (Xteq - mu) / sd
predq = knn_predict(Xteq_n, Xtr_n, ytr, k=1)
print("降采样预测:", list(zip([m['block']+':'+m['class'] for m in mq], predq)))

# ---------- 留一块出 CV（训练块内部，报告支持数） ----------
cv_rows = train
lo_probs = []
for hold in sorted(set(r["block"] for r in cv_rows)):
    tr = [r for r in cv_rows if r["block"] != hold]
    te = [r for r in cv_rows if r["block"] == hold]
    if not te or not tr: continue
    A, ya, _ = build_set(tr); B, yb, mb = build_set(te)
    m2, s2 = A.mean(0), A.std(0)+1e-6
    A_n=(A-m2)/s2; B_n=(B-m2)/s2
    p = knn_predict(B_n, A_n, ya, k=1)
    for g, pp, mm in zip(yb, p, mb):
        lo_probs.append((mm["block"], g, pp))

# ---------- 汇总指标 ----------
all_classes = sorted(set(r["class"] for r in labels))
support = collections.Counter(r["class"] for r in labels)
rows_out = []
for c in all_classes:
    rows_out.append({"class": c, "support": support[c]})

# 测试集(80px) 混淆
import collections as C
cm = C.Counter()
for g, p in zip(yte, pred):
    cm[(g, p)] += 1

# 保存结果json
res = {
    "train_blocks": sorted(TRAIN_BLKS), "test_blocks": sorted(TEST_BLKS),
    "labels_total": len(labels),
    "classes": all_classes, "support": dict(support),
    "test_gt_pred": [{"gt": g, "pred": p, "block": m["block"]} for g, p, m in zip(yte, pred, mte)],
    "quarter_pred": [{"gt": g, "pred": p, "block": m["block"]} for g, p, m in zip(yteq, predq, mq)],
    "loo": lo_probs,
}
json.dump(res, open(os.path.join(ROOT, "out", "recog", "clf_result.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("done")
