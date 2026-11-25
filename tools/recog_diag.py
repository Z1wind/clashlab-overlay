# -*- coding: utf-8 -*-
# recog_diag.py — 诊断 v2：紧框物体模板 + 多尺度，排除源块后 top 得分（纯离线）
import json, os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BLK = os.path.join(ROOT, "out", "overlay", "blocks")
log = json.load(open(os.path.join(BLK, "collect_log.json"), encoding="utf-8"))
blocks = {}
for t in log["tiles"]:
    blocks[t["file"].replace(".png", "")] = cv2.imdecode(
        np.fromfile(os.path.join(BLK, t["file"]), dtype=np.uint8), cv2.IMREAD_COLOR)

# 紧框：只包物体本体
SEEDS = [
    ("法师塔_wizard", "b10", (300, 190, 380, 340)),
    ("迫击炮_mortar", "b09", (190, 50, 260, 200)),
    ("X连弩_xbow", "b11", (600, 140, 260, 190)),
    ("空气炮_dome", "b10", (0, 40, 260, 280)),
    ("红金棘塔_待考", "b04", (430, 280, 240, 260)),
    ("四锥塔_待考", "b11", (150, 20, 250, 240)),
    ("紫金塔_待考", "b13", (10, 130, 180, 380)),
    ("白堡塔_待考", "b05", (370, 150, 220, 270)),
    ("加农炮_locked", "b14", (770, 50, 180, 200)),
    ("链锅_待考", "b09", (240, 340, 260, 210)),
]
SCALES = [0.92, 1.0, 1.08]

def prep(im):
    # 灰度 + 归一化亮度
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    return g

for label, src, box in SEEDS:
    sx, sy, sw, sh = box
    tpl = prep(blocks[src])[sy:sy + sh, sx:sx + sw]
    rows = []
    for fn, im in blocks.items():
        if fn == src:
            continue
        g = prep(im)
        best = -1.0; bl = None
        for sc in SCALES:
            tw, th = max(8, int(sw * sc)), max(8, int(sh * sc))
            if tw >= g.shape[1] or th >= g.shape[0]:
                continue
            tsc = cv2.resize(tpl, (tw, th), interpolation=cv2.INTER_AREA if sc < 1 else cv2.INTER_CUBIC)
            res = cv2.matchTemplate(g, tsc, cv2.TM_CCOEFF_NORMED)
            _, mx, _, ml = cv2.minMaxLoc(res)
            if mx > best:
                best, bl = float(mx), ml
        rows.append((fn, round(best, 3), bl))
    rows.sort(key=lambda r: -r[1])
    print(f"\n== {label} (src={src}) ==")
    for fn, s, ml in rows[:5]:
        print(f"  {fn}: {s} @ {ml}")
