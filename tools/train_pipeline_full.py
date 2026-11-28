# -*- coding: utf-8 -*-
"""在全部好数据上训练 门控+类型 并导出 ONNX（给桌面版预标注用）。"""
import json, os, random, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import cv2, numpy as np, torch, torch.nn as nn
from tools.apk_export_to_dataset import load_export
from clashlab.geo import Calib
S = 96
paths = [os.path.join(os.path.expanduser("~"), "Downloads", "annot_b%02d.json" % i) for i in range(1, 9)]
bases = []
for bi, p in enumerate(paths):
    if bi in (0, 1): continue
    d = json.load(open(p, encoding="utf-8"))
    img = cv2.imdecode(np.fromfile(os.path.join(BASE, "android", "assets", d["image"]), np.uint8), cv2.IMREAD_COLOR)
    wn, hn = d["image_size"]; quad = np.float32([[u*wn, v*hn] for u, v in d["corners_norm"]])
    cal = Calib.from_quad(quad, n=44)
    centers = [(b["type"], b["tile"][0]+.5, b["tile"][1]+.5) for b in d["buildings"]]
    bases.append({"img": img, "cal": cal, "centers": centers})
print("bases", len(bases), flush=True)
types = sorted({t for b in bases for (t,_,_) in b["centers"]}); TIDX = {t:i for i,t in enumerate(types)}
print("types", len(types), flush=True)
def crop(img, cal, tx, ty):
    x0, y0 = tx-1.5, ty-1.5
    p = [cal.tile_to_px(x0,y0), cal.tile_to_px(x0+4,y0), cal.tile_to_px(x0+4,y0+4), cal.tile_to_px(x0,y0+4)]
    H = cv2.getPerspectiveTransform(np.float32(p), np.float32([[0,0],[S,0],[S,S],[0,S]]))
    return cv2.warpPerspective(img, H, (S,S), flags=cv2.INTER_AREA)
def aug(c, r):
    x = c.astype(np.float32)*r.uniform(0.85,1.15)+r.uniform(-12,12); x=np.clip(x,0,255)
    M = cv2.getRotationMatrix2D((S/2,S/2), r.uniform(-4,4), r.uniform(0.92,1.08))
    M[0,2]+=r.uniform(-3,3); M[1,2]+=r.uniform(-3,3)
    x = cv2.warpAffine(x, M, (S,S), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return x.astype(np.uint8)
class Net(nn.Module):
    def __init__(self, n):
        super().__init__()
        def blk(i,o): return nn.Sequential(nn.Conv2d(i,o,3,padding=1), nn.BatchNorm2d(o), nn.ReLU(True), nn.MaxPool2d(2))
        self.f = nn.Sequential(blk(3,32), blk(32,64), blk(64,128), blk(128,192), nn.AdaptiveAvgPool2d(1))
        self.drop = nn.Dropout(0.25); self.head = nn.Linear(192, n)
    def forward(self, x): return self.head(self.drop(self.f(x).flatten(1)))
def batch(items, DEV):
    xs = np.stack([c for c,_ in items])[:, :, :, ::-1]
    x = torch.from_numpy(xs.copy()).permute(0,3,1,2).float().div(255).to(DEV)
    y = torch.tensor([l for _,l in items], dtype=torch.long).to(DEV)
    return x, y
rng = random.Random(7); DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# gate
gpos, gneg = [], []
for b in bases:
    for (t,cx,cy) in b["centers"]: gpos.append((crop(b["img"], b["cal"], cx, cy), 1))
    tries = 0
    while tries < 12000 and len(gneg) < 110*len(bases):
        tries += 1
        cx = rng.uniform(1.5,42.5); cy = rng.uniform(1.5,42.5)
        if any(abs(cx-ox)+abs(cy-oy)<2.2 for (_,ox,oy) in b["centers"]): continue
        gneg.append((crop(b["img"], b["cal"], cx, cy), 0))
gate = Net(2).to(DEV); opt = torch.optim.AdamW(gate.parameters(), lr=2e-3, weight_decay=2e-4)
lossf = nn.CrossEntropyLoss(weight=torch.tensor([1.0,3.0], device=DEV), label_smoothing=0.03)
for ep in range(30):
    gate.train(); rng.shuffle(gpos); rng.shuffle(gneg)
    for it in range(max(1,(len(gpos)+len(gneg))//80)):
        items = [(aug(c,rng),l) for (c,l) in [gpos[rng.randrange(len(gpos))] for _ in range(40)] + [gneg[rng.randrange(len(gneg))] for _ in range(40)]]
        x,y = batch(items, DEV); loss = lossf(gate(x), y); opt.zero_grad(); loss.backward(); opt.step()
print("gate trained", flush=True)
# type
tpos = []
for b in bases:
    for (t,cx,cy) in b["centers"]: tpos.append((crop(b["img"], b["cal"], cx, cy), TIDX[t]))
tnet = Net(len(types)).to(DEV); opt2 = torch.optim.AdamW(tnet.parameters(), lr=2e-3, weight_decay=2e-4)
lossf2 = nn.CrossEntropyLoss(label_smoothing=0.03)
for ep in range(30):
    tnet.train(); rng.shuffle(tpos)
    for it in range(max(1,len(tpos)//64)):
        items = [(aug(c,rng),l) for (c,l) in [tpos[rng.randrange(len(tpos))] for _ in range(64)]]
        x,y = batch(items, DEV); loss = lossf2(tnet(x), y); opt2.zero_grad(); loss.backward(); opt2.step()
print("type trained", flush=True)
torch.save({"model": gate.state_dict(), "size": S}, os.path.join(BASE,"models","pipeline_gate.pt"))
torch.save({"model": tnet.state_dict(), "types": types, "size": S}, os.path.join(BASE,"models","pipeline_type.pt"))
print("saved pt models")
# 导出 ONNX
gate.eval(); tnet.eval()
dummy = torch.randn(1,3,S,S, device=DEV)
torch.onnx.export(gate, dummy, os.path.join(BASE,"models","pipeline_gate.onnx"), input_names=["input"], output_names=["logits"], opset_version=18)
torch.onnx.export(tnet, dummy, os.path.join(BASE,"models","pipeline_type.onnx"), input_names=["input"], output_names=["logits"], opset_version=18)
print("saved onnx models", flush=True)
