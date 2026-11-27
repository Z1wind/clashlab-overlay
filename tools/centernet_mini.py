# -*- coding: utf-8 -*-
"""CenterNet-mini：纯 torch 检测器（热图+尺寸），不依赖 torchvision 算子。
数据：datasets/detect（已排除 firespitter/wall）。"""
import glob, math, os, random, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import torch, torch.nn as nn, torch.nn.functional as F
import cv2, numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
D = os.path.join(BASE, "datasets", "detect")
OUT = os.path.join(BASE, "out", "detect_runs", "centernet")
os.makedirs(OUT, exist_ok=True)
NAMES = []
for l in open(os.path.join(D, "data.yaml"), encoding="utf-8"):
    s = l.strip()
    if s and s[0].isdigit() and ":" in s:
        NAMES.append(s.split(":", 1)[1].strip())
NC = len(NAMES); S = 640; ST = 4; HS = S // ST
print("classes", NC, "in", S, "hm", HS, flush=True)
dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def load(split):
    return sorted(glob.glob(os.path.join(D, "images", split, "*.jpg")))
train, val = load("train"), load("val")
print("train", len(train), "val", len(val), "device", dev, flush=True)

def gauss(radius):
    r = max(1, int(radius))
    y, x = np.ogrid[-r:r + 1, -r:r + 1]
    return np.exp(-(x * x + y * y) / (2 * (r / 2.0) ** 2))

def target_of(lab_path):
    hm = np.zeros((NC, HS, HS), np.float32)
    sz = np.zeros((2, HS, HS), np.float32)
    wh = np.zeros((NC, 2), np.float32)
    cnt = np.zeros(NC, np.float32)
    if not os.path.exists(lab_path): return hm, sz
    for ln in open(lab_path, encoding="utf-8"):
        t = ln.split()
        if len(t) != 5: continue
        c = int(t[0]); cx, cy, bw, bh = [float(v) for v in t[1:]]
        gx = min(HS - 1, max(0, int(cx * HS))); gy = min(HS - 1, max(0, int(cy * HS)))
        rr = max(2, int(min(bw, bh) * HS))
        g = gauss(rr)[: HS - max(0, gy - rr), : HS - max(0, gx - rr)]
        g = g[: min(g.shape[0], 2 * rr + 1), : min(g.shape[1], 2 * rr + 1)]
        y0 = max(0, gy - rr); x0 = max(0, gx - rr)
        patch = hm[c, y0:y0 + g.shape[0], x0:x0 + g.shape[1]]
        np.maximum(patch, g, out=patch)
        sz[:, gy, gx] = [bw * S, bh * S]
        wh_temp = wh[c]; wh_temp += [bw * S, bh * S]; wh[c] = wh_temp
        cnt[c] += 1
    return hm, sz

def batch(paths, idxs):
    imgs, hms, szs = [], [], []
    for i in idxs:
        p = paths[i]
        im = cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)
        im = cv2.resize(im, (S, S))
        imgs.append(im[:, :, ::-1].astype(np.float32) / 255.0)
        hm, sz = target_of(os.path.join(D, "labels", os.path.basename(p)[:-4] + ".txt"))
        hms.append(hm); szs.append(sz)
    x = torch.from_numpy(np.stack(imgs)).permute(0, 3, 1, 2)
    return x.to(dev), torch.from_numpy(np.stack(hms)).to(dev), torch.from_numpy(np.stack(szs)).to(dev)

class Net(nn.Module):
    def __init__(self):
        super().__init__()
        def blk(a, b):
            return nn.Sequential(nn.Conv2d(a, b, 3, 1, 1), nn.BatchNorm2d(b), nn.ReLU(inplace=True),
                                 nn.Conv2d(b, b, 3, 1, 1), nn.BatchNorm2d(b), nn.ReLU(inplace=True))
        self.d1 = blk(3, 24); self.d2 = blk(24, 48); self.d3 = blk(48, 96); self.d4 = blk(96, 128)
        self.p1 = nn.MaxPool2d(2); self.p2 = nn.MaxPool2d(2)
        self.up = nn.Upsample(scale_factor=2, mode="bilinear", align_corners=False)
        self.head = nn.Sequential(nn.Conv2d(128, 96, 3, 1, 1), nn.ReLU(inplace=True), nn.Conv2d(96, NC + 2, 1))
    def forward(self, x):
        x = self.p1(self.d1(x)); x = self.p2(self.d2(x))
        x = self.d3(x)   # 96ch @160
        x = self.d4(x)   # 128ch @160
        return self.head(x)

net = Net().to(dev)
opt = torch.optim.AdamW(net.parameters(), lr=2e-3)
EPOCHS = 16; BS = 8
t0 = time.time()
def focal(pred, gt):
    pred = torch.clamp(pred, 1e-4, 1 - 1e-4)
    pos = gt.eq(1).float(); neg = 1 - pos
    pos_loss = -torch.log(pred) * (1 - pred) ** 2 * pos
    neg_loss = -torch.log(1 - pred) * pred ** 2 * neg
    return (pos_loss.sum() + neg_loss.sum()) / (pos.sum() + 1)
for ep in range(EPOCHS):
    random.shuffle(train); tot = 0.0; n = 0
    for b in range(0, len(train) - BS + 1, BS):
        x, hm, sz = batch(train, range(b, b + BS))
        out = net(x)
        ph = torch.sigmoid(out[:, :NC]); ps = out[:, NC:NC + 2]
        l1 = focal(ph, hm)
        mask = (hm.max(dim=1, keepdim=True)[0] > 0.9).float()
        l2 = (torch.abs(ps - sz) * mask).sum() / (mask.sum() * 2 + 1e-6)
        loss = l1 + l2 * 0.2
        opt.zero_grad(); loss.backward(); opt.step()
        tot += float(loss); n += 1
        if n % 60 == 0:
            print("ep%d it%d/%d loss=%.4f (%.0fs)" % (ep, n, len(train) // BS, tot / n, time.time() - t0), flush=True)
    torch.save({"model": net.state_dict(), "names": NAMES}, os.path.join(OUT, "epoch%d.pt" % (ep + 1)))
    print("epoch", ep + 1, "loss", round(tot / max(1, n), 4), flush=True)
torch.save({"model": net.state_dict(), "names": NAMES}, os.path.join(OUT, "last.pt"))
print("TRAIN_DONE", flush=True)
