# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "auto_candidates.py")
t = open(p, encoding="utf-8").read()
if "_GATE" not in t:
    # 1) 门控加载
    t = t.replace("_MODEL = None\n_LOAD_ERR = None",
                  "_MODEL = None\n_LOAD_ERR = None\n_GATE = None\n_GATE_ERR = None")
    # 2) 在 _load 后加 _load_gate
    anchor = "def _classify_batch(torch, net, batch):"
    add = '''def _load_gate():
    """建筑/背景门控模型（可选）。不存在则返回 None。"""
    global _GATE, _GATE_ERR
    if _GATE is not None or _GATE_ERR is not None:
        return _GATE
    path = os.path.join(BASE, "models", "building_gate.pt")
    if not os.path.exists(path):
        _GATE_ERR = "no building_gate.pt"
        return None
    try:
        import torch
        import torch.nn as nn
        ck = torch.load(path, map_location="cpu", weights_only=False)

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

        net = Gate()
        net.load_state_dict(ck["model"])
        net.eval()
        _GATE = (torch, net)
        return _GATE
    except Exception as e:
        _GATE_ERR = str(e)[:160]
        return None


def _gate_batch(torch, net, batch):
    """返回每个窗口属于「建筑」的概率。"""
    import numpy as np
    arr = np.ascontiguousarray(batch[:, :, :, ::-1])
    x = torch.from_numpy(arr).permute(0, 3, 1, 2).float().div(255)
    with torch.no_grad():
        logit = net(x)
        prob = torch.softmax(logit, 1)[:, 1].cpu().numpy()
    return prob


''' + anchor
    t = t.replace(anchor, add, 1)
    # 3) 在 candidates 主循环里插入门控
    old = '''        if not warps:
            continue
        for i in range(0, len(warps), 512):
            batch = np.stack(warps[i:i + 512])
            for (ti, conf), (x, y) in zip(_classify_batch(torch, net, batch), tiles[i:i + 512]):'''
    new = '''        if not warps:
            continue
        picked_warps, picked_tiles = warps, tiles
        if gate:
            gp = []
            for i in range(0, len(warps), 512):
                gp.extend(_gate_batch(gate[0], gate[1], np.stack(warps[i:i + 512])).tolist())
            gated_counts[size] = int(sum(1 for v in gp if v >= gate_thr))
            keep = [j for j, v in enumerate(gp) if v >= gate_thr]
            picked_warps = [warps[j] for j in keep]
            picked_tiles = [tiles[j] for j in keep]
        if not picked_warps:
            continue
        for i in range(0, len(picked_warps), 512):
            batch = np.stack(picked_warps[i:i + 512])
            for (ti, conf), (x, y) in zip(_classify_batch(torch, net, batch), picked_tiles[i:i + 512]):'''
    if old in t:
        t = t.replace(old, new, 1)
        # gate 变量与统计初始化（在 sizes 循环前）
        t = t.replace('''    items = []
    sizes = (2, 3, 4)''', '''    items = []
    gate = _load_gate()
    gate_thr = 0.85
    gated_counts = {}
    sizes = (2, 3, 4)''')
        # 返回信息里加 gate 统计
        t = t.replace('''    return {"ok": True, "items": picked, "total_before_dedupe": len(items),
            "note": "实验性候选，必须人工确认后再用"}''',
'''    return {"ok": True, "items": picked, "total_before_dedupe": len(items),
            "gate_used": bool(gate), "gate_threshold": gate_thr, "gated_counts": gated_counts,
            "note": "实验性候选，必须人工确认后再用"}''')
        open(p, "w", encoding="utf-8", newline="\n").write(t)
        print("candidates gated")
    else:
        print("loop anchor miss")
else:
    print("already gated")
