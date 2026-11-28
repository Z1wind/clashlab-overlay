# -*- coding: utf-8 -*-
"""直接检查 .pt 门控/embedding 在 b03 真实建筑中心 vs 随机位置的得分。"""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import cv2, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
from clashlab.geo import Calib
S = 96
class Net(nn.Module):
    def __init__(self, n):
        super().__init__()
        def blk(i,o): return nn.Sequential(nn.Conv2d(i,o,3,padding=1), nn.BatchNorm2d(o), nn.ReLU(True), nn.MaxPool2d(2))
        self.f = nn.Sequential(blk(3,32), blk(32,64), blk(64,128), blk(128,192), nn.AdaptiveAvgPool2d(1))
        self.drop = nn.Dropout(0.2); self.head = nn.Linear(192, n)
    def forward(self, x): return self.head(self.drop(self.f(x).flatten(1)))
class Emb(nn.Module):
    def __init__(self, n, dim=128):
        super().__init__()
        def blk(i,o): return nn.Sequential(nn.Conv2d(i,o,3,padding=1), nn.BatchNorm2d(o), nn.ReLU(True), nn.MaxPool2d(2))
        self.f = nn.Sequential(blk(3,32), blk(32,64), blk(64,128), blk(128,192), nn.AdaptiveAvgPool2d(1))
        self.drop = nn.Dropout(0.2); self.proj = nn.Linear(192, dim); self.weight = nn.Parameter(torch.randn(n, dim))
    def forward(self, x): return F.normalize(self.proj(self.drop(self.f(x).flatten(1))), dim=1)
gk = torch.load(os.path.join(BASE,"models","hybrid_gate.pt"), map_location="cpu")
ek = torch.load(os.path.join(BASE,"models","hybrid_emb.pt"), map_location="cpu")
gate = Net(2); gate.load_state_dict(gk["model"]); gate.eval()
emb = Emb(ek["nc"]); emb.load_state_dict(ek["model"]); emb.eval()
d = json.load(open(os.path.join(os.path.expanduser("~"), "Downloads", "annot_b03.json"), encoding="utf-8"))
img = cv2.imdecode(np.fromfile(os.path.join(BASE, "android", "assets", d["image"]), np.uint8), cv2.IMREAD_COLOR)
wn, hn = d["image_size"]; quad = np.float32([[u*wn, v*hn] for u, v in d["corners_norm"]])
cal = Calib.from_quad(quad, n=44)
def crop(cx, cy):
    x0, y0 = cx-1.5, cy-1.5
    p = [cal.tile_to_px(x0,y0), cal.tile_to_px(x0+4,y0), cal.tile_to_px(x0+4,y0+4), cal.tile_to_px(x0,y0+4)]
    H = cv2.getPerspectiveTransform(np.float32(p), np.float32([[0,0],[S,0],[S,S],[0,S]]))
    return cv2.warpPerspective(img, H, (S,S), flags=cv2.INTER_AREA)
def probs(cells):
    xs = np.stack([crop(cx, cy) for (cx,cy) in cells])[:,:,:,::-1].copy()
    x = torch.from_numpy(xs).permute(0,3,1,2).float().div(255)
    with torch.no_grad():
        gp = torch.softmax(gate(x), 1)[:,1].numpy()
    return gp
gt_cells = [(b["tile"][0], b["tile"][1]) for b in d["buildings"]]
rand_cells = [(np.random.uniform(2,42), np.random.uniform(2,42)) for _ in range(200)]
gp_gt = probs(gt_cells); gp_r = probs(rand_cells)
print("GT building centers gate prob: mean %.3f >0.5: %.2f >0.85: %.2f" % (gp_gt.mean(), (gp_gt>0.5).mean(), (gp_gt>0.85).mean()))
print("random cells gate prob:        mean %.3f >0.5: %.2f >0.85: %.2f" % (gp_r.mean(), (gp_r>0.5).mean(), (gp_r>0.85).mean()))
# embedding 分离度
P = np.load(os.path.join(BASE,"models","hybrid_protos.npz"))["P"]; PC = np.load(os.path.join(BASE,"models","hybrid_protos.npz"))["PC"]
xs = np.stack([crop(cx,cy) for (cx,cy) in gt_cells])[:,:,:,::-1].copy()
x = torch.from_numpy(xs).permute(0,3,1,2).float().div(255)
with torch.no_grad(): e = emb(x).numpy()
sim = e @ P.T
print("embedding best-sim at GT: mean %.3f" % sim.max(1).mean())
