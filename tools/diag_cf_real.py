# -*- coding: utf-8 -*-
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import torch, torch.nn as nn, torch.nn.functional as F
import cv2, numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ck = torch.load(os.path.join(BASE, "out", "detect_runs", "cf", "last.pt"), map_location="cpu")
NAMES = ck["names"]; NC = len(NAMES); S = 320; ST = 4
dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
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
net = Net().to(dev); net.load_state_dict(ck["model"]); net.eval()
for name in ("enemy_scout_live.png",):
    img = cv2.imdecode(np.fromfile(os.path.join(BASE, "out", "live", name), np.uint8), cv2.IMREAD_COLOR)
    x = torch.from_numpy(cv2.resize(img, (S, S))[:, :, ::-1].astype(np.float32) / 255.0).permute(2, 0, 1)[None].to(dev)
    with torch.no_grad():
        out = net(x); hm = torch.sigmoid(out[:, :NC])[0]
    print(name, "hm max", round(float(hm.max()), 4), "mean", round(float(hm.mean()), 5))
    vals, idx = hm.flatten().topk(8)
    for v, i in zip(vals.tolist(), idx.tolist()):
        c = i // (hm.shape[1] * hm.shape[2]); rem = i % (hm.shape[1] * hm.shape[2])
        print("  top", NAMES[c], round(v, 4))
