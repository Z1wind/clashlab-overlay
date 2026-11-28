# -*- coding: utf-8 -*-
"""实验A：分类器多seed集成 + TTA（5 shift），8 基留一对比。"""
import json, os, random, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import cv2, numpy as np, torch, torch.nn as nn
from clashlab.geo import Calib
S = 112; SEED_N = 2
def prep(path):
    d = json.load(open(path, encoding="utf-8"))
    img = cv2.imdecode(np.fromfile(os.path.join(BASE, "android", "assets", d["image"]), np.uint8), cv2.IMREAD_COLOR)
    wn, hn = d["image_size"]; quad = np.float32([[u*wn, v*hn] for u, v in d["corners_norm"]])
    cal = Calib.from_quad(quad, n=44)
    crops = []
    for b in d["buildings"]:
        x, y = b["tile"]; cx, cy = x + .5, y + .5
        x0, y0 = cx - 2.0, cy - 2.0
        p = [cal.tile_to_px(x0,y0), cal.tile_to_px(x0+4,y0), cal.tile_to_px(x0+4,y0+4), cal.tile_to_px(x0,y0+4)]
        H = cv2.getPerspectiveTransform(np.float32(p), np.float32([[0,0],[S,0],[S,S],[0,S]]))
        crops.append(cv2.warpPerspective(img, H, (S,S), flags=cv2.INTER_AREA))
    return crops, [(b["type"], b["tile"][0], b["tile"][1]) for b in d["buildings"]]
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
def to_t(xs, dev):
    x = np.stack(xs)[:, :, :, ::-1].copy()
    return torch.from_numpy(x).permute(0,3,1,2).float().div(255).to(dev)
def main():
    paths = [os.path.join(os.path.expanduser("~"), "Downloads", "annot_b01 (1).json"),
             os.path.join(os.path.expanduser("~"), "Downloads", "annot_b02 (1).json")]
    paths += [os.path.join(os.path.expanduser("~"), "Downloads", "annot_b%02d.json" % i) for i in range(3, 9)]
    data = [prep(p) for p in paths]
    types = sorted({t for _, labs in data for (t,_,_) in labs}); TIDX = {t:i for i,t in enumerate(types)}
    DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("types", len(types), "device", DEV, flush=True)
    accs = []
    for hold in range(len(data)):
        tr_crops, tr_lab = [], []
        for i,(cs, labs) in enumerate(data):
            if i == hold: continue
            tr_crops += cs; tr_lab += [TIDX[t] for t,_,_ in labs]
        va_crops, va_lab = data[hold]
        va_y = [TIDX[t] for t,_,_ in va_lab]
        nets = []
        for seed in range(SEED_N):
            rng = random.Random(7 + seed); torch.manual_seed(7 + seed)
            net = Net(len(types)).to(DEV)
            opt = torch.optim.AdamW(net.parameters(), lr=2e-3, weight_decay=2e-4)
            lossf = nn.CrossEntropyLoss(label_smoothing=0.05)
            idx = list(range(len(tr_crops)))
            for ep in range(32):
                net.train(); rng.shuffle(idx)
                for it in range(max(1, len(idx)//64)):
                    sel = idx[it*64:(it+1)*64]
                    xs = [aug(tr_crops[i], rng) for i in sel]
                    x = to_t(xs, DEV)
                    y = torch.tensor([tr_lab[i] for i in sel], dtype=torch.long).to(DEV)
                    loss = lossf(net(x), y); opt.zero_grad(); loss.backward(); opt.step()
            net.eval(); nets.append(net)
        def predict(crops, tta):
            outs = []
            with torch.no_grad():
                for net in nets:
                    probs = []
                    if tta:
                        for dx, dy in ((0,0),(4,0),(-4,0),(0,4),(0,-4)):
                            xs = []
                            for c in crops:
                                M = np.float32([[1,0,dx],[0,1,dy]])
                                xs.append(cv2.warpAffine(c, M, (S,S), borderMode=cv2.BORDER_REFLECT))
                            probs.append(torch.softmax(net(to_t(xs, DEV)), 1).cpu().numpy())
                        probs = np.mean(probs, 0)
                    else:
                        probs = torch.softmax(net(to_t(crops, DEV)), 1).cpu().numpy()
                    outs.append(probs)
            return np.mean(outs, 0)
        def acc(p):
            pred = p.argmax(1)
            top1 = float((pred == np.array(va_y)).mean())
            top3 = float(np.mean([y in p[k].argsort()[-3:] for k, y in enumerate(va_y)]))
            return top1, top3
        a0 = acc(predict(va_crops, False))
        a1 = acc(predict(va_crops, True))
        print("hold %d: base(top1=%.3f top3=%.3f) tta(top1=%.3f top3=%.3f)" % (data[hold][1][0][1] if False else hold, a0[0], a0[1], a1[0], a1[1]), flush=True)
        accs.append((a0[0], a0[1], a1[0], a1[1]))
    m = lambda i: sum(a[i] for a in accs)/len(accs)
    print("ENSEMBLE MEAN base top1=%.3f top3=%.3f | TTA top1=%.3f top3=%.3f" % (m(0), m(1), m(2), m(3)))
    json.dump({"mean": {"base_top1": m(0), "base_top3": m(1), "tta_top1": m(2), "tta_top3": m(3)},
               "folds": accs}, open(os.path.join(BASE,"out","cls_ensemble_report.json"), "w", encoding="utf-8"), indent=1)
if __name__ == "__main__":
    main()
