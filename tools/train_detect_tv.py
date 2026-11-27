# -*- coding: utf-8 -*-
"""合成数据集训练轻量检测器（FasterRCNN-MobileNetV3，从零起）。排除 firespitter 已在数据层完成。"""
import glob, os, random, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import torch, torchvision
from torch.utils.data import Dataset, DataLoader
import cv2, numpy as np
from torchvision.models.detection import fasterrcnn_mobilenet_v3_large_fpn
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
D = os.path.join(BASE, "datasets", "detect")
OUTDIR = os.path.join(BASE, "out", "detect_runs", "tv")
os.makedirs(OUTDIR, exist_ok=True)
NAMES = [l.split(":", 1)[1].strip() for l in open(os.path.join(D, "data.yaml"), encoding="utf-8") if l.strip().startswith(tuple(str(i) + ":" for i in range(60)))]
print("classes:", len(NAMES), flush=True)
SEED = 7; random.seed(SEED); torch.manual_seed(SEED)

class DS(Dataset):
    def __init__(self, split):
        self.imgs = sorted(glob.glob(os.path.join(D, "images", split, "*.jpg")))
        self.labs = os.path.join(D, "labels", split)
    def __len__(self): return len(self.imgs)
    def __getitem__(self, i):
        p = self.imgs[i]
        img = cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)[:, :, ::-1].copy()
        h, w = img.shape[:2]
        boxes, labels = [], []
        lp = os.path.join(self.labs, os.path.basename(p).replace(".jpg", ".txt"))
        if os.path.exists(lp):
            for ln in open(lp, encoding="utf-8"):
                t = ln.split()
                if len(t) != 5: continue
                c, cx, cy, bw, bh = int(t[0]), float(t[1]), float(t[2]), float(t[3]), float(t[4])
                boxes.append([(cx - bw / 2) * w, (cy - bh / 2) * h, (cx + bw / 2) * w, (cy + bh / 2) * h])
                labels.append(c + 1)
        if boxes:
            b = torch.tensor(boxes, dtype=torch.float32); l = torch.tensor(labels, dtype=torch.int64)
        else:
            b = torch.zeros((0, 4), dtype=torch.float32); l = torch.zeros((0,), dtype=torch.int64)
        return torch.from_numpy(img).permute(2, 0, 1).float() / 255.0, {"boxes": b, "labels": l}

def collate(batch): return tuple(zip(*batch))

tr = DS("train"); va = DS("val")
print("train:", len(tr), "val:", len(va), flush=True)
dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("device:", dev, flush=True)
net = fasterrcnn_mobilenet_v3_large_fpn(weights=None, weights_backbone=None, num_classes=len(NAMES) + 1)
net.to(dev)
opt = torch.optim.SGD([p for p in net.parameters() if p.requires_grad], lr=0.01, momentum=0.9, weight_decay=5e-4)
dl = DataLoader(tr, batch_size=4, shuffle=True, collate_fn=collate, num_workers=0)
EPOCHS = 8
t0 = time.time()
best = 0.0
for ep in range(EPOCHS):
    net.train(); tot = 0.0; n = 0
    for it, (imgs, tg) in enumerate(dl):
        imgs = [im.to(dev) for im in imgs]; tg = [{k: v.to(dev) for k, v in t.items()} for t in tg]
        loss = net(imgs, tg)
        lossv = sum(loss.values())
        opt.zero_grad(); lossv.backward(); opt.step()
        tot += float(lossv); n += 1
        if it % 50 == 0:
            print("ep%d it%d/%d loss=%.3f (%.0fs)" % (ep, it, len(dl), tot / max(1, n), time.time() - t0), flush=True)
    torch.save({"model": net.state_dict(), "names": NAMES},
               os.path.join(OUTDIR, "epoch%d.pt" % (ep + 1)))
    print("epoch", ep + 1, "done, loss", round(tot / max(1, n), 3), flush=True)
torch.save({"model": net.state_dict(), "names": NAMES}, os.path.join(OUTDIR, "last.pt"))
print("TRAIN_DONE", OUTDIR, flush=True)
