# -*- coding: utf-8 -*-
"""CenterNet-fast 真实战图推理 + 可视化。"""
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
src = os.path.join(BASE, "out", "live", "enemy_scout_live.png")
img = cv2.imdecode(np.fromfile(src, np.uint8), cv2.IMREAD_COLOR)
inp = cv2.resize(img, (S, S))[:, :, ::-1].astype(np.float32) / 255.0
x = torch.from_numpy(inp).permute(2, 0, 1)[None].to(dev)
with torch.no_grad():
    out = net(x); hm = torch.sigmoid(out[:, :NC])[0]; sz = out[0, NC:NC + 2]
hmax = F.max_pool2d(hm[None], 3, 1, 1)[0]
peaks = (hmax == hm) & (hm > 0.60)
idx = torch.nonzero(peaks).tolist()
items = []
for c, y, xx in idx:
    conf = float(hm[c, y, xx]); w = float(sz[0, y, xx]); h = float(sz[1, y, xx])
    w = max(w, 48.0); h = max(h, 48.0)  # 尺寸头未收敛时给兜底框
    cx = (xx + 0.5) * ST * (img.shape[1] / S); cy = (y + 0.5) * ST * (img.shape[0] / S)
    w *= img.shape[1] / S; h *= img.shape[0] / S
    items.append((conf, c, cx, cy, w, h))
items.sort(reverse=True); items = items[:60]
vis = img.copy(); counts = {}
for conf, c, cx, cy, w, h in items:
    counts[NAMES[c]] = counts.get(NAMES[c], 0) + 1
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    cv2.rectangle(vis, (x0, y0), (int(cx + w / 2), int(cy + h / 2)), (0, 0, 255), 2)
    cv2.putText(vis, NAMES[c][:10] + " %.2f" % conf, (x0, max(12, y0 - 3)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)
print("detections:", sum(counts.values()))
for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
    print("  ", k, v)
p = os.path.join(BASE, "out", "live", "detect_cf_eval.png")
cv2.imencode(".png", vis)[1].tofile(p)
print("saved", p)
