# -*- coding: utf-8 -*-
"""半自动标注候选：用已训练的「类型+等级」分类器在 44×44 网格上滑窗，
给出候选建筑（实验性，需人工确认）。torch 不可用时 available()=False。"""
from __future__ import annotations
import os
import sys

BASE = os.environ.get("CLASHLAB_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MODEL = None
_LOAD_ERR = None


def available():
    try:
        import torch  # noqa: F401
        return os.path.exists(os.path.join(BASE, "models", "synth_level.pt"))
    except Exception:
        return False


class _Net:
    pass


def _load():
    global _MODEL, _LOAD_ERR
    if _MODEL is not None or _LOAD_ERR is not None:
        return _MODEL
    try:
        import torch
        import torch.nn as nn

        ck = torch.load(os.path.join(BASE, "models", "synth_level.pt"), map_location="cpu", weights_only=False)
        types = ck["types"]

        class Net(nn.Module):
            def __init__(self):
                super().__init__()
                def blk(i, o):
                    return nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(True), nn.MaxPool2d(2))
                self.f = nn.Sequential(blk(3, 24), blk(24, 48), blk(48, 96), blk(96, 128), nn.AdaptiveAvgPool2d(1))
                self.drop = nn.Dropout(0.2)
                self.type_head = nn.Linear(128, len(types))
                self.level_head = nn.Linear(128, 1)

            def forward(self, x):
                h = self.drop(self.f(x).flatten(1))
                return self.type_head(h), torch.sigmoid(self.level_head(h)).squeeze(1)

        net = Net()
        net.load_state_dict(ck["state_dict"])
        net.eval()
        _MODEL = (torch, net, types)
        return _MODEL
    except Exception as e:
        _LOAD_ERR = str(e)[:200]
        return None


def _classify_batch(torch, net, batch):
    """batch: numpy (N,96,96,3) BGR -> list[(type,conf)]."""
    import numpy as np
    arr = np.ascontiguousarray(batch[:, :, :, ::-1])
    x = torch.from_numpy(arr).permute(0, 3, 1, 2).float().div(255)
    with torch.no_grad():
        logit, _ = net(x)
        prob = torch.softmax(logit, 1).cpu().numpy()
    out = []
    for row in prob:
        i = int(row.argmax())
        out.append((i, float(row[i])))
    return out


def _flatness(gray):
    import cv2
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def candidates(image_path, quad, max_n=30, min_conf=0.97, min_var=60.0):
    """返回 [{type,tile:[x,y],size,conf}]（最多 max_n 个，按 conf 降序）。"""
    if not available():
        return {"ok": False, "error": "torch/model 不可用（仅源码环境支持，exe 内置版不含 torch）", "items": []}
    m = _load()
    if not m:
        return {"ok": False, "error": "模型加载失败: " + str(_LOAD_ERR), "items": []}
    torch, net, types = m
    import cv2
    import numpy as np
    sys.path.insert(0, BASE)
    from clashlab.geo import Calib
    from clashlab.assets import STATS
    img = cv2.imdecode(np.fromfile(image_path, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return {"ok": False, "error": "图片读取失败", "items": []}
    q = np.asarray(quad, np.float32).reshape(4, 2)
    cal = Calib.from_quad(q, n=44)
    DST = np.float32([[0, 0], [96, 0], [96, 96], [0, 96]])
    items = []
    sizes = (2, 3, 4)
    for size in sizes:
        tiles, warps = [], []
        for y in range(0, 44 - size + 1):
            for x in range(0, 44 - size + 1):
                p = [cal.tile_to_px(x, y), cal.tile_to_px(x + size, y),
                     cal.tile_to_px(x + size, y + size), cal.tile_to_px(x, y + size)]
                H = cv2.getPerspectiveTransform(np.float32(p), DST)
                w = cv2.warpPerspective(img, H, (96, 96), flags=cv2.INTER_AREA)
                if _flatness(cv2.cvtColor(w, cv2.COLOR_BGR2GRAY)) < min_var:
                    continue
                tiles.append((x, y)); warps.append(w)
        if not warps:
            continue
        for i in range(0, len(warps), 512):
            batch = np.stack(warps[i:i + 512])
            for (ti, conf), (x, y) in zip(_classify_batch(torch, net, batch), tiles[i:i + 512]):
                if conf < min_conf:
                    continue
                typ = types[ti]
                st = STATS.get(typ) or {}
                want = st.get("size")
                if want and int(want) != size:
                    continue
                items.append({"type": typ, "tile": [x, y], "size": size, "conf": round(conf, 4)})
    items.sort(key=lambda d: -d["conf"])
    picked = []
    for it in items:
        if all(abs(it["tile"][0] - p["tile"][0]) > max(1, it["size"] // 2) or
               abs(it["tile"][1] - p["tile"][1]) > max(1, it["size"] // 2) for p in picked):
            picked.append(it)
        if len(picked) >= max_n:
            break
    return {"ok": True, "items": picked, "total_before_dedupe": len(items),
            "note": "实验性候选，必须人工确认后再用"}
