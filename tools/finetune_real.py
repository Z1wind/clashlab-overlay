# -*- coding: utf-8 -*-
"""真实域微调：类型分类器 + 建筑门控；留出 defence_17 作为验证。"""
import json, os, random, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np, torch, torch.nn as nn
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("device:", DEV, flush=True)
arr = np.load(os.path.join(BASE, "datasets", "real_layout", "imgs.npy"))
labels = json.load(open(os.path.join(BASE, "datasets", "real_layout", "labels.json"), encoding="utf-8"))
VAL_IMG = "defence_17.jpg"
tr_idx = [i for i, l in enumerate(labels) if l["image"] != VAL_IMG]
va_idx = [i for i, l in enumerate(labels) if l["image"] == VAL_IMG]
print("train", len(tr_idx), "val", len(va_idx), flush=True)

def batch(idxs, shuffle=False):
    ids = list(idxs)
    if shuffle:
        random.shuffle(ids)
    xs = np.stack([arr[i][:, :, ::-1] for i in ids])
    x = torch.from_numpy(xs).permute(0, 3, 1, 2).float().div(255)
    y = [labels[i] for i in ids]
    return x.to(DEV), y

class TypeNet(nn.Module):
    def __init__(self, n_types):
        super().__init__()
        def blk(i, o):
            return nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(True), nn.MaxPool2d(2))
        self.f = nn.Sequential(blk(3, 24), blk(24, 48), blk(48, 96), blk(96, 128), nn.AdaptiveAvgPool2d(1))
        self.drop = nn.Dropout(0.2)
        self.type_head = nn.Linear(128, n_types)
        self.level_head = nn.Linear(128, 1)
    def forward(self, x):
        h = self.drop(self.f(x).flatten(1))
        return self.type_head(h), torch.sigmoid(self.level_head(h)).squeeze(1)

ck = torch.load(os.path.join(BASE, "models", "synth_level.pt"), map_location="cpu", weights_only=False)
TYPES = ck["types"]; TIDX = {t: i for i, t in enumerate(TYPES)}

def type_acc(net, idxs):
    net.eval(); correct = total = 0; top3 = 0
    with torch.no_grad():
        for i in range(0, len(idxs), 128):
            x, ys = batch(idxs[i:i+128])
            logit, _ = net(x)
            for row, lab in zip(logit.cpu().numpy(), ys):
                t = lab["type"]
                if t not in TIDX:
                    continue
                order = row.argsort()[::-1]
                total += 1
                if order[0] == TIDX[t]:
                    correct += 1
                if TIDX[t] in order[:3]:
                    top3 += 1
    return correct / max(1, total), top3 / max(1, total), total

net = TypeNet(len(TYPES)).to(DEV); net.load_state_dict(ck["state_dict"])
p_tr = [i for i in tr_idx if labels[i]["type"] in TIDX]
a1 = type_acc(net, va_idx)
print("baseline type top1/top3:", round(a1[0], 3), round(a1[1], 3), "n=", a1[2], flush=True)
opt = torch.optim.AdamW(net.parameters(), lr=4e-4)
lossf = nn.CrossEntropyLoss()
t0 = time.time(); BS = 64
for ep in range(8):
    random.shuffle(p_tr)
    tot = n = 0
    for i in range(0, len(p_tr) - BS + 1, BS):
        x, ys = batch(p_tr[i:i+BS])
        y = torch.tensor([TIDX[l["type"]] for l in ys], dtype=torch.long).to(DEV)
        loss = lossf(net(x)[0], y)
        opt.zero_grad(); loss.backward(); opt.step()
        tot += float(loss.detach()); n += 1
    print("type ep%d loss=%.3f (%.0fs)" % (ep, tot / max(1, n), time.time() - t0), flush=True)
a2 = type_acc(net, va_idx)
print("after top1/top3:", round(a2[0], 3), round(a2[1], 3), flush=True)
torch.save({"model": net.state_dict(), "types": TYPES, "val_top1": a2[0], "val_top3": a2[1],
            "note": "fine-tuned on real layout crops (4 bases train, defence_17 val)"},
           os.path.join(BASE, "models", "real_type.pt"))
print("saved models/real_type.pt", flush=True)

# ---- 门控微调（真实域）----
class Gate(nn.Module):
    def __init__(self):
        super().__init__()
        def blk(i, o):
            return nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(True), nn.MaxPool2d(2))
        self.f = nn.Sequential(blk(3, 24), blk(24, 48), blk(48, 96), blk(96, 128), nn.AdaptiveAvgPool2d(1))
        self.drop = nn.Dropout(0.2)
        self.head = nn.Linear(128, 2)
    def forward(self, x):
        return self.head(self.drop(self.f(x).flatten(1)))

gck = torch.load(os.path.join(BASE, "models", "building_gate.pt"), map_location="cpu", weights_only=False)
gate = Gate().to(DEV); gate.load_state_dict(gck["model"])

def gate_eval(net, idxs):
    net.eval(); tp = fp = tn = fn = 0
    with torch.no_grad():
        for i in range(0, len(idxs), 256):
            x, ys = batch(idxs[i:i+256])
            prob = torch.softmax(net(x), 1)[:, 1].cpu().numpy()
            for p, lab in zip(prob, ys):
                pos = lab["type"] != "__bg__"
                pred = p >= 0.85
                if pos and pred: tp += 1
                elif pos: fn += 1
                elif pred: fp += 1
                else: tn += 1
    prec = tp / max(1, tp + fp); rec = tp / max(1, tp + fn)
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn, "precision": round(prec, 3), "recall": round(rec, 3),
            "accuracy": round((tp + tn) / max(1, tp + tn + fp + fn), 3)}

b = gate_eval(gate, va_idx)
print("gate baseline on val:", b, flush=True)
opt2 = torch.optim.AdamW(gate.parameters(), lr=3e-4)
for ep in range(5):
    random.shuffle(tr_idx)
    tot = n = 0
    for i in range(0, len(tr_idx) - BS + 1, BS):
        x, ys = batch(tr_idx[i:i+BS])
        y = torch.tensor([0 if l["type"] == "__bg__" else 1 for l in ys], dtype=torch.long).to(DEV)
        loss = lossf(gate(x), y)
        opt2.zero_grad(); loss.backward(); opt2.step()
        tot += float(loss.detach()); n += 1
    print("gate ep%d loss=%.3f" % (ep, tot / max(1, n)), flush=True)
a = gate_eval(gate, va_idx)
print("gate after on val:", a, flush=True)
torch.save({"model": gate.state_dict(), "size": 96, "val": a,
            "note": "fine-tuned on real layout crops (4 bases train, defence_17 val)"},
           os.path.join(BASE, "models", "building_gate_real.pt"))
print("saved models/building_gate_real.pt", flush=True)
json.dump({"type_baseline": a1[:2], "type_after": a2[:2], "gate_baseline": b, "gate_after": a},
          open(os.path.join(BASE, "models", "real_finetune_metrics.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("DONE", flush=True)
