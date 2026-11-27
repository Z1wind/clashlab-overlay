# -*- coding: utf-8 -*-
"""渲染图格点分类器：用 5 张手工标注训练，留 b05(defence17) 验证。
正样本：GT 建筑位置的 4x4 窗口；负样本：随机非建筑格。
"""
import glob, json, os, random, re, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np, torch, torch.nn as nn
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab.geo import Calib
DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")
S = 96
PAIRS = [  # (annotated json, image)
 ("01_annotated.json", "b01.jpg"), ("03_annotated.json", "b02.jpg"),
 ("04_annotated.json", "b03.jpg"), ("05_annotated.json", "b04.jpg"),
 ("06_annotated.json", "b05.jpg"),
]
VAL_IMG = "b05.jpg"

def quad_from_note(note, img_w):
    m = re.search(r"quad=\[\[([^\]]+)\],\[([^\]]+)\],\[([^\]]+)\],\[([^\]]+)\]\]", note or "")
    if not m: return None
    q = np.array([[float(v) for v in g.split(",")] for g in m.groups()], np.float32)
    return q * (img_w / 2622.0)

def crop4(img, cal, x, y):
    x0 = max(0, x - 1); y0 = max(0, y - 1); x1 = min(44, x0 + 4); y1 = min(44, y0 + 4)
    x0 = max(0, x1 - 4); y0 = max(0, y1 - 4)
    p = [cal.tile_to_px(x0, y0), cal.tile_to_px(x1, y0), cal.tile_to_px(x1, y1), cal.tile_to_px(x0, y1)]
    H = cv2.getPerspectiveTransform(np.float32(p), np.float32([[0,0],[S,0],[S,S],[0,S]]))
    return cv2.warpPerspective(img, H, (S, S), flags=cv2.INTER_AREA)

samples = []  # (crop, type or '__bg__')
random.seed(7); np.random.seed(7)
for ann_name, img_name in PAIRS:
    ann = json.load(open(os.path.join(BASE, "out", "annotate", ann_name), encoding="utf-8"))
    img_p = os.path.join(BASE, "android", "assets", "img", img_name)
    img = cv2.imdecode(np.fromfile(img_p, np.uint8), cv2.IMREAD_COLOR)
    quad = quad_from_note(ann.get("note"), img.shape[1])
    cal = Calib.from_quad(quad, n=44)
    occ = set()
    pos = 0
    for b in ann["buildings"]:
        t = b["type"]; x, y = int(b["tile"][0]), int(b["tile"][1])
        for dx in range(2):
            for dy in range(2): occ.add((x+dx, y+dy))
        samples.append((crop4(img, cal, x, y), t, img_name)); pos += 1
    neg = 0; tries = 0
    while neg < 500 and tries < 6000:
        tries += 1
        x = random.randint(0, 41); y = random.randint(0, 41)
        if any((x+dx, y+dy) in occ for dx in range(2) for dy in range(2)): continue
        samples.append((crop4(img, cal, x, y), "__bg__", img_name)); neg += 1
    print(img_name, "pos", pos, "neg", neg, flush=True)

types = sorted({s[1] for s in samples if s[1] != "__bg__"})
TIDX = {t: i for i, t in enumerate(types)}
N = len(types) + 1  # +bg
print("types:", len(types), "samples:", len(samples), flush=True)

class Net(nn.Module):
    def __init__(self, n):
        super().__init__()
        def blk(i, o): return nn.Sequential(nn.Conv2d(i,o,3,padding=1), nn.BatchNorm2d(o), nn.ReLU(True), nn.MaxPool2d(2))
        self.f = nn.Sequential(blk(3,32), blk(32,64), blk(64,128), blk(128,192), nn.AdaptiveAvgPool2d(1))
        self.drop = nn.Dropout(0.2); self.head = nn.Linear(192, n)
    def forward(self, x): return self.head(self.drop(self.f(x).flatten(1)))

train = [s for s in samples if s[2] != VAL_IMG]
val = [s for s in samples if s[2] == VAL_IMG]
print("train", len(train), "val", len(val), flush=True)

def batch(items):
    xs = np.stack([s[0][:, :, ::-1] for s in items])
    x = torch.from_numpy(xs).permute(0,3,1,2).float().div(255).to(DEV)
    y = torch.tensor([N-1 if s[1]=="__bg__" else TIDX[s[1]] for s in items], dtype=torch.long).to(DEV)
    return x, y

net = Net(N).to(DEV)
opt = torch.optim.AdamW(net.parameters(), lr=2e-3)
lossf = nn.CrossEntropyLoss()
BS = 64; t0 = time.time()
for ep in range(10):
    random.shuffle(train); tot = n = 0
    for i in range(0, len(train), BS):
        x, y = batch(train[i:i+BS])
        loss = lossf(net(x), y); opt.zero_grad(); loss.backward(); opt.step()
        tot += float(loss.detach()); n += 1
    # val acc（含 bg）
    net.eval(); ok = totn = 0; tp = fn = fp = tnn = 0
    with torch.no_grad():
        for i in range(0, len(val), 128):
            x, y = batch(val[i:i+128]); pred = net(x).argmax(1)
            for t_, p_ in zip(y.cpu().numpy(), pred.cpu().numpy()):
                ok += int(t_ == p_); totn += 1
                is_bg = (t_ == N-1); pred_bg = (p_ == N-1)
                if not is_bg and not pred_bg: tp += 1
                elif not is_bg and pred_bg: fn += 1
                elif is_bg and not pred_bg: fp += 1
                else: tnn += 1
    net.train()
    print("ep%d loss %.3f val_acc %.3f | 建筑召回 %.3f 误报率 %.3f (%.0fs)" % (
        ep, tot/max(1,n), ok/max(1,totn), tp/max(1,tp+fn), fp/max(1,fp+tnn), time.time()-t0), flush=True)
os.makedirs(os.path.join(BASE, "models"), exist_ok=True)
torch.save({"model": net.state_dict(), "types": types, "bg": "__bg__"}, os.path.join(BASE, "models", "render_tile_cls.pt"))
print("saved models/render_tile_cls.pt", flush=True)
