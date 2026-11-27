# -*- coding: utf-8 -*-
"""滑窗自动标注：用 synth_level 类型分类器在 44x44 网格上按足迹尺寸滑窗。"""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np, torch, torch.nn as nn
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab.geo import Calib
from clashlab.assets import STATS
IMG = os.path.join(BASE, "out", "live", "enemy_scout_live.png")
SIZE = 96; N = 44
ck = torch.load(os.path.join(BASE, "models", "synth_level.pt"), map_location="cpu", weights_only=False)
TYPES = ck["types"]; TIDX = {t: i for i, t in enumerate(TYPES)}
dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class Net(nn.Module):
    def __init__(self):
        super().__init__()
        def blk(i, o):
            return nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(True), nn.MaxPool2d(2))
        self.f = nn.Sequential(blk(3, 24), blk(24, 48), blk(48, 96), blk(96, 128), nn.AdaptiveAvgPool2d(1))
        self.drop = nn.Dropout(0.2)
        self.type_head = nn.Linear(128, len(TYPES))
        self.level_head = nn.Linear(128, 1)
    def forward(self, x):
        h = self.drop(self.f(x).flatten(1))
        return self.type_head(h), torch.sigmoid(self.level_head(h)).squeeze(1)

net = Net().to(dev); net.load_state_dict(ck["state_dict"]); net.eval()
img = cv2.imdecode(np.fromfile(IMG, np.uint8), cv2.IMREAD_COLOR)
quad = np.array([[640.0, 52.0], [1120.0, 352.0], [640.0, 652.0], [178.0, 352.0]], np.float32)
cal = Calib.from_quad(quad, n=N)
DST = np.float32([[0, 0], [SIZE, 0], [SIZE, SIZE], [0, SIZE]])

def warps(size):
    tiles = [(x, y) for y in range(0, N - size + 1) for x in range(0, N - size + 1)]
    out = np.empty((len(tiles), SIZE, SIZE, 3), np.uint8)
    for k, (x, y) in enumerate(tiles):
        p = [cal.tile_to_px(x, y), cal.tile_to_px(x + size, y), cal.tile_to_px(x + size, y + size), cal.tile_to_px(x, y + size)]
        H = cv2.getPerspectiveTransform(np.float32(p), DST)
        out[k] = cv2.warpPerspective(img, H, (SIZE, SIZE), flags=cv2.INTER_AREA)
    return tiles, out

cands = []
for size in (2, 3, 4):
    tiles, arr = warps(size)
    for i in range(0, len(arr), 1024):
        batch = np.ascontiguousarray(arr[i:i + 1024][:, :, :, ::-1])
        x = torch.from_numpy(batch).permute(0, 3, 1, 2).float().div(255).to(dev)
        with torch.no_grad():
            logit, lv = net(x)
            prob = torch.softmax(logit, 1).cpu().numpy()
            lvv = lv.cpu().numpy()
        for j in range(prob.shape[0]):
            ci = int(prob[j].argmax()); conf = float(prob[j, ci])
            if conf < 0.90:
                continue
            t = TYPES[ci]
            if t not in STATS:
                continue
            want = STATS[t].get("size")
            if want and int(want) != size:
                continue
            x_, y_ = tiles[i + j]
            cands.append((conf, t, x_, y_, size, int(round(lvv[j] * (STATS[t].get("level") or 15)))))
print("candidates:", len(cands))
keep = []
for conf, t, x, y, size, lv in sorted(cands, reverse=True):
    if any(k[1] == t and abs(k[2] - x) <= max(1, size // 2) and abs(k[3] - y) <= max(1, size // 2) for k in keep):
        continue
    if any(abs(k[2] - x) <= 1 and abs(k[3] - y) <= 1 and k[1] != t for k in keep):
        continue
    keep.append((conf, t, x, y, size, lv))
print("kept:", len(keep))
for k in keep[:30]:
    print("  ", k)
vis = img.copy()
for conf, t, x, y, size, lv in keep:
    p0 = cal.tile_to_px(x, y); p1 = cal.tile_to_px(x + size, y); p2 = cal.tile_to_px(x + size, y + size); p3 = cal.tile_to_px(x, y + size)
    pts = np.array([p0, p1, p2, p3], np.int32)
    cv2.polylines(vis, [pts], True, (0, 0, 255), 2)
    c = cal.tile_to_px(x + size / 2, y + size / 2)
    cv2.putText(vis, "%s %.2f" % (t[:9], conf), (int(c[0]) - 20, int(c[1])), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)
cv2.imencode(".png", vis)[1].tofile(os.path.join(BASE, "out", "live", "auto_annotate.png"))
ann = {"name": "shadow_th17_auto", "grid": N, "quad": quad.tolist(), "source": "sliding-window-classifier",
       "buildings": [{"type": t, "tile": [x, y], "level": lv, "conf": round(conf, 3), "source": "auto"} for conf, t, x, y, size, lv in keep]}
open(os.path.join(BASE, "out", "annotate", "shadow_th17_auto_annotated.json"), "w", encoding="utf-8").write(json.dumps(ann, ensure_ascii=False, indent=1))
print("saved auto_annotate.png + json")
