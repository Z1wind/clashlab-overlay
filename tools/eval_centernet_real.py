# -*- coding: utf-8 -*-
"""CenterNet-mini 在真实战图上推理：热图峰值 + 尺寸回归，输出可视化与命中统计。"""
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import torch, torch.nn as nn, torch.nn.functional as F
import cv2, numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
CK = os.path.join(BASE, "out", "detect_runs", "centernet", "last.pt")
S = 640; ST = 4
ck = torch.load(CK, map_location="cuda" if torch.cuda.is_available() else "cpu")
NAMES = ck["names"]; NC = len(NAMES)
dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
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
net = Net().to(dev); net.load_state_dict(ck["model"]); net.eval()
img = cv2.imdecode(np.fromfile(os.path.join(BASE, "out", "live", "enemy_scout_live.png"), np.uint8), cv2.IMREAD_COLOR)
inp = cv2.resize(img, (S, S))[:, :, ::-1].astype(np.float32) / 255.0
x = torch.from_numpy(inp).permute(2, 0, 1)[None].to(dev)
with torch.no_grad():
    out = net(x)
    hm = torch.sigmoid(out[:, :NC])[0]
    sz = out[0, NC:]
hmax = F.max_pool2d(hm[None], 3, 1, 1)[0]
peaks = (hmax == hm) & (hm > 0.25)
idx = torch.nonzero(peaks)  # [N,3] (c,y,x)
vis = img.copy()
counts = {}
items = []
for c, y, x_ in idx.tolist():
    conf = float(hm[c, y, x_]); w = float(sz[0, y, x_]); h = float(sz[1, y, x_])
    cx = (x_ + 0.5) * ST; cy = (y + 0.5) * ST
    sc = img.shape[1] / float(S)
    cx, cy, w, h = cx * sc, cy * sc, w * sc, h * sc
    items.append((conf, c, cx, cy, w, h))
items.sort(reverse=True)
items = items[:60]
for conf, c, cx, cy, w, h in items:
    if w < 12 or h < 12: continue
    counts[NAMES[c]] = counts.get(NAMES[c], 0) + 1
    x0, y0, x1, y1 = int(cx - w / 2), int(cy - h / 2), int(cx + w / 2), int(cy + h / 2)
    col = (0, 0, 255) if "air" in NAMES[c] else (0, 255, 255)
    cv2.rectangle(vis, (x0, y0), (x1, y1), col, 2)
    cv2.putText(vis, NAMES[c][:12] + " %.2f" % conf, (x0, max(12, y0 - 3)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, col, 1)
print("detections:", sum(counts.values()), "classes:", len(counts))
for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
    print("  ", k, v)
outp = os.path.join(BASE, "out", "live", "detect_eval_centernet.png")
cv2.imencode(".png", vis)[1].tofile(outp)
print("saved", outp)
