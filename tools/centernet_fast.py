# -*- coding: utf-8 -*-
"""CenterNet-fast：320px / 17 类关键防御 / batch16，纯 torch。"""
import glob, os, random, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import torch, torch.nn as nn, torch.nn.functional as F
import cv2, numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
D = os.path.join(BASE, "datasets", "detect")
OUT = os.path.join(BASE, "out", "detect_runs", "cf")
os.makedirs(OUT, exist_ok=True)
ALL = []
for l in open(os.path.join(D, "data.yaml"), encoding="utf-8"):
    s = l.strip()
    if s and s[0].isdigit() and ":" in s:
        ALL.append(s.split(":", 1)[1].strip())
WANT = {"air_defense", "air_sweeper", "monolith", "eagle_artillery", "scattershot", "town_hall",
        "x-bow", "inferno_tower", "wizard_tower", "cannon", "archer_tower", "mortar",
        "clan_castle", "spell_tower", "bomb_tower", "multi-archer_tower", "hidden_tesla"}
KEY = [k for k in ALL if k in WANT]
IDX = {ALL.index(k): i for i, k in enumerate(KEY)}
NC = len(KEY); S = 320; ST = 4; HS = S // ST
print("classes", NC, "of", len(ALL), "size", S, "hm", HS, flush=True)
dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
train = sorted(glob.glob(os.path.join(D, "images", "train", "*.jpg")))
val = sorted(glob.glob(os.path.join(D, "images", "val", "*.jpg")))
print("train", len(train), "device", dev, flush=True)

def gauss(r):
    r = max(1, int(r)); y, x = np.ogrid[-r:r + 1, -r:r + 1]
    return np.exp(-(x * x + y * y) / (2 * (r / 2.0) ** 2))

def target_of(path):
    hm = np.zeros((NC, HS, HS), np.float32); sz = np.zeros((2, HS, HS), np.float32)
    # labels 在 labels/<split>/ 下，不在 images 下
    lp = path.replace(os.sep + "images" + os.sep, os.sep + "labels" + os.sep)[:-4] + ".txt"
    if os.path.exists(lp):
        for ln in open(lp, encoding="utf-8"):
            t = ln.split()
            if len(t) != 5: continue
            c = int(t[0])
            if c not in IDX: continue
            ci = IDX[c]
            cx, cy, bw, bh = [float(v) for v in t[1:]]
            gx = min(HS - 1, max(0, int(cx * HS))); gy = min(HS - 1, max(0, int(cy * HS)))
            rr = max(1, int(min(bw, bh) * HS))
            g = gauss(rr); gh, gw = g.shape
            y0 = max(0, gy - rr); x0 = max(0, gx - rr)
            gy0 = y0 - (gy - rr); gx0 = x0 - (gx - rr)
            patch = hm[ci, y0:y0 + min(gh - gy0, HS - y0), x0:x0 + min(gw - gx0, HS - x0)]
            sub = g[gy0:gy0 + patch.shape[0], gx0:gx0 + patch.shape[1]]
            np.maximum(patch, sub, out=patch)
            sz[:, gy, gx] = [bw * S, bh * S]
    return hm, sz

def get_batch(idxs):
    imgs, hms, szs = [], [], []
    for i in idxs:
        p = train[i]
        im = cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)
        im = cv2.resize(im, (S, S))
        imgs.append(im[:, :, ::-1].astype(np.float32) / 255.0)
        a, b = target_of(p); hms.append(a); szs.append(b)
    return (torch.from_numpy(np.stack(imgs)).permute(0, 3, 1, 2).to(dev),
            torch.from_numpy(np.stack(hms)).to(dev), torch.from_numpy(np.stack(szs)).to(dev))

class Net(nn.Module):
    def __init__(self):
        super().__init__()
        def blk(a, b):
            return nn.Sequential(nn.Conv2d(a, b, 3, 1, 1), nn.BatchNorm2d(b), nn.ReLU(inplace=True),
                                 nn.Conv2d(b, b, 3, 1, 1), nn.BatchNorm2d(b), nn.ReLU(inplace=True))
        self.d1 = blk(3, 24); self.d2 = blk(24, 48); self.d3 = blk(48, 96); self.d4 = blk(96, 128)
        self.p1 = nn.MaxPool2d(2); self.p2 = nn.MaxPool2d(2)
        self.head = nn.Sequential(nn.Conv2d(128, 96, 3, 1, 1), nn.ReLU(inplace=True), nn.Conv2d(96, NC + 2, 1))
    def forward(self, x):
        x = self.p1(self.d1(x)); x = self.p2(self.d2(x)); x = self.d3(x); x = self.d4(x)
        return self.head(x)

net = Net().to(dev)
opt = torch.optim.AdamW(net.parameters(), lr=3e-3)
EPOCHS = 12; BS = 16
def focal(pred, gt):
    pred = torch.clamp(pred, 1e-4, 1 - 1e-4)
    pos = gt.eq(1).float(); neg = 1 - pos
    return (-torch.log(pred) * (1 - pred) ** 2 * pos).sum() / (pos.sum() + 1) + \
           (-torch.log(1 - pred) * pred ** 2 * neg).sum() / (neg.sum() + 1)
t0 = time.time()
for ep in range(EPOCHS):
    random.shuffle(train); tot = 0.0; n = 0
    for b in range(0, len(train) - BS + 1, BS):
        x, hm, sz = get_batch(range(b, b + BS))
        out = net(x)
        ph = torch.sigmoid(out[:, :NC]); ps = out[:, NC:NC + 2]
        mask = (hm.max(dim=1, keepdim=True)[0] > 0.9).float()
        loss = focal(ph, hm) + 0.2 * (torch.abs(ps - sz) * mask).sum() / (mask.sum() * 2 + 1e-6)
        opt.zero_grad(); loss.backward(); opt.step()
        tot += float(loss.detach()); n += 1
        if n % 30 == 0:
            print("ep%d it%d/%d loss=%.4f (%.0fs)" % (ep, n, len(train) // BS, tot / n, time.time() - t0), flush=True)
    torch.save({"model": net.state_dict(), "names": KEY}, os.path.join(OUT, "epoch%d.pt" % (ep + 1)))
    print("epoch", ep + 1, "loss", round(tot / max(1, n), 4), flush=True)
torch.save({"model": net.state_dict(), "names": KEY}, os.path.join(OUT, "last.pt"))
print("TRAIN_DONE", flush=True)
