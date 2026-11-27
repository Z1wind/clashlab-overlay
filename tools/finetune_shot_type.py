# -*- coding: utf-8 -*-
"""用「图片 + quad + tile/size + type」标注微调类型分类器（截图域）。

labels JSON 格式：
{
  "quad": [[x,y],[x,y],[x,y],[x,y]],
  "items": [{"image": "out/live/war1080/base_01.png", "tile": [x,y], "size": 3, "type": "inferno-tower"}]
}
未标 __bg__ 的视为背景负类，仅用于统计；分类器只用建筑类型。
"""
import argparse, json, os, random, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
import cv2, numpy as np, torch, torch.nn as nn
DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")
S = 96


def crop(img, cal, x, y, size):
    side = max(4, size + 2)
    pad = (side - size) // 2
    x0 = max(0, x - pad); y0 = max(0, y - pad)
    x1 = min(44, x0 + side); y1 = min(44, y0 + side)
    x0 = max(0, x1 - side); y0 = max(0, y1 - side)
    p = [cal.tile_to_px(x0, y0), cal.tile_to_px(x1, y0), cal.tile_to_px(x1, y1), cal.tile_to_px(x0, y1)]
    H = cv2.getPerspectiveTransform(np.float32(p), np.float32([[0, 0], [S, 0], [S, S], [0, S]]))
    return cv2.warpPerspective(img, H, (S, S), flags=cv2.INTER_AREA)


class Net(nn.Module):
    def __init__(self, n):
        super().__init__()
        def blk(i, o):
            return nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(True), nn.MaxPool2d(2))
        self.f = nn.Sequential(blk(3, 24), blk(24, 48), blk(48, 96), blk(96, 128), nn.AdaptiveAvgPool2d(1))
        self.drop = nn.Dropout(0.2)
        self.type_head = nn.Linear(128, n)
        self.level_head = nn.Linear(128, 1)

    def forward(self, x):
        h = self.drop(self.f(x).flatten(1))
        return self.type_head(h), torch.sigmoid(self.level_head(h)).squeeze(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", required=True)
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--out", default=os.path.join(BASE, "models", "real_shot_type.pt"))
    a = ap.parse_args()
    sys.path.insert(0, BASE)
    from clashlab.geo import Calib
    doc = json.load(open(a.labels, encoding="utf-8"))
    quad = np.float32(doc["quad"]) if doc.get("quad") else None
    items = [it for it in doc.get("items") or [] if it.get("type") and it["type"] != "__bg__"]
    imgs = {}
    samples = []
    for it in items:
        p = it["image"] if os.path.isabs(it["image"]) else os.path.join(BASE, it["image"])
        q = np.float32(it.get("quad") or quad)
        key = (p, tuple(map(tuple, q.tolist())))
        if key not in imgs:
            im = cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)
            imgs[key] = (im, Calib.from_quad(q, n=44))
        im, cal = imgs[key]
        samples.append((crop(im, cal, int(it["tile"][0]), int(it["tile"][1]), int(it.get("size") or 2)), it["type"], p))
    print("samples:", len(samples), "images:", len(imgs), flush=True)
    if len(samples) < 30:
        print("too few samples"); return 2
    ck = torch.load(os.path.join(BASE, "models", "synth_level.pt"), map_location="cpu", weights_only=False)
    TYPES = ck["types"]; TIDX = {t: i for i, t in enumerate(TYPES)}
    samples = [s for s in samples if s[1] in TIDX]
    print("usable:", len(samples), flush=True)
    rng = random.Random(7); rng.shuffle(samples)
    val_n = max(4, len(samples) // 5)
    val, train = samples[:val_n], samples[val_n:]
    net = Net(len(TYPES)).to(DEV); net.load_state_dict(ck["state_dict"])
    opt = torch.optim.AdamW(net.parameters(), lr=4e-4)
    lossf = nn.CrossEntropyLoss()
    def acc(split):
        net.eval(); ok = tot = 0
        with torch.no_grad():
            for i in range(0, len(split), 64):
                batch = split[i:i+64]
                xs = np.stack([b[0][:, :, ::-1] for b in batch])
                x = torch.from_numpy(xs).permute(0, 3, 1, 2).float().div(255).to(DEV)
                y = torch.tensor([TIDX[b[1]] for b in batch]).to(DEV)
                pred = net(x)[0].argmax(1)
                ok += int((pred == y).sum()); tot += len(batch)
        net.train()
        return ok / max(1, tot)
    print("baseline val top1:", round(acc(val), 3), flush=True)
    for ep in range(a.epochs):
        rng.shuffle(train); tot = n = 0
        for i in range(0, len(train), 32):
            batch = train[i:i+32]
            if len(batch) < 2:
                continue
            xs = np.stack([b[0][:, :, ::-1] for b in batch])
            x = torch.from_numpy(xs).permute(0, 3, 1, 2).float().div(255).to(DEV)
            y = torch.tensor([TIDX[b[1]] for b in batch]).to(DEV)
            loss = lossf(net(x)[0], y)
            opt.zero_grad(); loss.backward(); opt.step()
            tot += float(loss.detach()); n += 1
        print("ep%d loss %.3f val %.3f" % (ep, tot / max(1, n), acc(val)), flush=True)
    top1 = acc(val)
    torch.save({"model": net.state_dict(), "types": TYPES, "val_top1": top1,
                "note": "fine-tuned on labeled real screenshots"}, a.out)
    print("saved", a.out, "val_top1", round(top1, 3), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
