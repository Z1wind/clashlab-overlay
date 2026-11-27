# -*- coding: utf-8 -*-
"""重训渲染图格点分类器：平衡采样 + 背景降权。"""
import json, os, random, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np, torch, torch.nn as nn
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ITEMS = os.path.join(BASE, "out", "logs", "render_cls_items.npz")
# 复用上脚本生成的样本：上脚本没有保存样本，重新用其函数？改为直接读取已保存的模型？ 简单：导入上脚本逻辑太重。
# 这里重新构造（与上脚本相同，但保存 npz 供后续复用）
sys.path.insert(0, BASE)
import cv2
from clashlab.geo import Calib
import re
S = 96
PAIRS = [("01_annotated.json","b01.jpg"),("03_annotated.json","b02.jpg"),("04_annotated.json","b03.jpg"),
         ("05_annotated.json","b04.jpg"),("06_annotated.json","b05.jpg")]
VAL_IMG = "b05.jpg"
def quad_from_note(note, img_w):
    m = re.search(r"quad=\[\[([^\]]+)\],\[([^\]]+)\],\[([^\]]+)\],\[([^\]]+)\]\]", note or "")
    if not m: return None
    q = np.array([[float(v) for v in g.split(",")] for g in m.groups()], np.float32)
    return q * (img_w / 2622.0)
def crop4(img, cal, x, y):
    x0 = max(0, x-1); y0 = max(0, y-1); x1 = min(44, x0+4); y1 = min(44, y0+4)
    x0 = max(0, x1-4); y0 = max(0, y1-4)
    p = [cal.tile_to_px(x0,y0), cal.tile_to_px(x1,y0), cal.tile_to_px(x1,y1), cal.tile_to_px(x0,y1)]
    H = cv2.getPerspectiveTransform(np.float32(p), np.float32([[0,0],[S,0],[S,S],[0,S]]))
    return cv2.warpPerspective(img, H, (S,S), flags=cv2.INTER_AREA)
samples = []
random.seed(7); np.random.seed(7)
for ann_name, img_name in PAIRS:
    ann = json.load(open(os.path.join(BASE, "out", "annotate", ann_name), encoding="utf-8"))
    img = cv2.imdecode(np.fromfile(os.path.join(BASE, "android", "assets", "img", img_name), np.uint8), cv2.IMREAD_COLOR)
    quad = quad_from_note(ann.get("note"), img.shape[1]); cal = Calib.from_quad(quad, n=44)
    occ = set()
    for b in ann["buildings"]:
        x, y = int(b["tile"][0]), int(b["tile"][1])
        for dx in range(2):
            for dy in range(2): occ.add((x+dx, y+dy))
        samples.append((crop4(img, cal, x, y), b["type"], img_name))
    neg = 0
    while neg < 500:
        x = random.randint(0, 41); y = random.randint(0, 41)
        if any((x+dx, y+dy) in occ for dx in range(2) for dy in range(2)): continue
        samples.append((crop4(img, cal, x, y), "__bg__", img_name)); neg += 1
arr = np.stack([s[0] for s in samples], 0).astype(np.uint8)
json.dump([{"type": s[1], "img": s[2], "idx": i} for i, s in enumerate(samples)],
          open(os.path.join(BASE, "out", "logs", "render_cls_labels.json"), "w", encoding="utf-8"), ensure_ascii=False)
np.save(ITEMS.replace(".npz", "_imgs.npy"), arr)
print("samples", arr.shape, flush=True)
types = sorted({s[1] for s in samples if s[1] != "__bg__"}); TIDX = {t:i for i,t in enumerate(types)}
N = len(types) + 1
ys = np.array([N-1 if s[1]=="__bg__" else TIDX[s[1]] for s in samples])
imgs = [s[2] for s in samples]
tr = np.array([i for i in range(len(samples)) if imgs[i] != VAL_IMG])
va = np.array([i for i in range(len(samples)) if imgs[i] == VAL_IMG])
pos_tr = tr[ys[tr] != N-1]; bg_tr = tr[ys[tr] == N-1]
print("train pos", len(pos_tr), "bg", len(bg_tr), "val", len(va), "types", len(types), flush=True)
class Net(nn.Module):
    def __init__(self, n):
        super().__init__()
        def blk(i,o): return nn.Sequential(nn.Conv2d(i,o,3,padding=1), nn.BatchNorm2d(o), nn.ReLU(True), nn.MaxPool2d(2))
        self.f = nn.Sequential(blk(3,32), blk(32,64), blk(64,128), blk(128,192), nn.AdaptiveAvgPool2d(1))
        self.drop = nn.Dropout(0.2); self.head = nn.Linear(192, n)
    def forward(self, x): return self.head(self.drop(self.f(x).flatten(1)))
net = Net(N).to("cuda" if torch.cuda.is_available() else "cpu")
DEV = next(net.parameters()).device
weights = torch.ones(N, device=DEV); weights[N-1] = 0.15
opt = torch.optim.AdamW(net.parameters(), lr=1.5e-3)
lossf = nn.CrossEntropyLoss(weight=weights)
BS = 64
def make_batch(ids):
    xs = arr[ids][:, :, :, ::-1]
    x = torch.from_numpy(xs.copy()).permute(0,3,1,2).float().div(255).to(DEV)
    y = torch.from_numpy(ys[ids]).long().to(DEV)
    return x, y
t0 = time.time()
for ep in range(15):
    net.train()
    idx = np.concatenate([np.random.choice(pos_tr, 32, replace=True), np.random.choice(bg_tr, 32, replace=True)])
    np.random.shuffle(idx); tot = n = 0
    for i in range(0, len(idx), BS):
        x, y = make_batch(idx[i:i+BS])
        loss = lossf(net(x), y); opt.zero_grad(); loss.backward(); opt.step()
        tot += float(loss.detach()); n += 1
    net.eval(); corr = totn = tp = fn = fp = tn = 0
    with torch.no_grad():
        for i in range(0, len(va), 128):
            x, y = make_batch(va[i:i+128]); pred = net(x).argmax(1)
            for t_, p_ in zip(y.cpu().numpy(), pred.cpu().numpy()):
                corr += int(t_==p_); totn += 1
                if t_ != N-1 and p_ != N-1: tp += 1
                elif t_ != N-1: fn += 1
                elif p_ != N-1: fp += 1
                else: tn += 1
    print("ep%d loss %.3f acc %.3f | recall %.3f fp %.3f (%.0fs)" % (
        ep, tot/max(1,n), corr/max(1,totn), tp/max(1,tp+fn), fp/max(1,fp+tn), time.time()-t0), flush=True)
torch.save({"model": net.state_dict(), "types": types}, os.path.join(BASE, "models", "render_tile_cls_v2.pt"))
print("saved v2", flush=True)
