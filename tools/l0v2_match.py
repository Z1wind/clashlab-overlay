# -*- coding: utf-8 -*-
# l0v2_match.py — L0 双帧真跨帧（两遍法）：B抠->A搜定位 -> A该位置抠->B搜；双向peak+命中（纯离线）
import os, cv2, numpy as np, json
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OV = os.path.join(ROOT, "out", "overlay")
OUT = os.path.join(ROOT, "tools", "base_out", "v2")
A = cv2.imdecode(np.fromfile(os.path.join(OV, "v6_l0_two_shot_base.png"), dtype=np.uint8), cv2.IMREAD_COLOR)
B = cv2.imdecode(np.fromfile(os.path.join(OV, "v6_l0_three_shot_base.png"), dtype=np.uint8), cv2.IMREAD_COLOR)
H = np.array(json.load(open(os.path.join(ROOT, "tools", "base_out", "align_H.json"), encoding="utf-8"))["H"])
ga, gb = cv2.cvtColor(A, cv2.COLOR_BGR2GRAY), cv2.cvtColor(B, cv2.COLOR_BGR2GRAY)

SEEDS = [
    ("金仓_goldstor",   (660, 640), 46, 1),
    ("圣水收集器_elix", (610, 455), 34, 1),
    ("黑油罐_darkstor", (690, 480), 40, 1),
    ("箭塔_archer",     (620, 420), 36, 1),
    ("大本营_townhall", (505, 755), 44, 1),
    ("金收集器_goldcol",(500, 250), 34, 1),
    ("紫收集器_purpcol",(330, 300), 34, 1),
    ("迫击炮_mortar",   (600, 620), 34, 1),
    ("加农炮_cannon",   (600, 560), 36, 1),
    ("白堡塔2_archer2", (295, 380), 34, 1),
]
SCALES = [0.97, 1.0, 1.03]
HIT = 0.60

def search(img, tpl, sc_list, thresh, nmsr):
    hits = []; best = -1.0; bl = None
    for sc in sc_list:
        th = max(12, int(tpl.shape[0] * sc)); tw = max(12, int(tpl.shape[1] * sc))
        if th >= img.shape[0] or tw >= img.shape[1]:
            continue
        t = cv2.resize(tpl, (tw, th), interpolation=cv2.INTER_AREA if sc < 1 else cv2.INTER_CUBIC)
        res = cv2.matchTemplate(img, t, cv2.TM_CCOEFF_NORMED)
        _, mx, _, ml = cv2.minMaxLoc(res)
        if mx > best:
            best, bl = float(mx), (ml[0], ml[1], tw, th, sc)
        ys, xs = np.where(res >= thresh)
        for y, x in zip(ys, xs):
            hits.append((int(x), int(y), float(res[y, x]), sc))
    hits.sort(key=lambda h: -h[2])
    keep = []
    for x, y, s, sc in hits:
        if all((x - kx) ** 2 + (y - ky) ** 2 > nmsr ** 2 for kx, ky, *_ in keep):
            keep.append((x, y, s, sc))
    return best, bl, keep

results = []
ev = {}
for label, (cx, cy), h, expect in SEEDS:
    boxB = gb[cy - h:cy + h, cx - h:cx + h]
    # pass1 B -> A
    best_BA, bl_BA, keep_BA = search(ga, boxB, SCALES, HIT, 48)
    # 用 pass1 最佳位置抠 A 模板（同尺寸）
    best_AB, bl_AB, keep_AB = None, None, []
    if bl_BA and best_BA >= HIT:
        ax, ay, aw, ah, _ = bl_BA
        atpl = ga[ay:ay + ah, ax:ax + aw]
        best_AB, bl_AB, keep_AB = search(gb, atpl, SCALES, HIT, 48)
    row = dict(label=label, expect=expect,
               peak_BA=round(best_BA, 4), hits_BA=len(keep_BA), loc_BA=bl_BA[:2] if bl_BA else None,
               peak_AB=(round(best_AB, 4) if best_AB else None),
               hits_AB=len(keep_AB), loc_AB=bl_AB[:2] if bl_AB else None,
               Bbox=(cx - h, cy - h, 2 * h, 2 * h))
    results.append(row)
    ev[label] = dict(bl_BA=bl_BA, bl_AB=bl_AB, Bbox=row["Bbox"])
    print(f"{label}: B->A peak={row['peak_BA']} hits={row['hits_BA']} @{row['loc_BA']} | "
          f"A->B peak={row['peak_AB']} hits={row['hits_AB']} @{row['loc_AB']}")

# 证据图：左B框 右A最佳（再A->B框）
for label, e in ev.items():
    x0, y0, w, hh = e["Bbox"]
    left = B.copy()
    cv2.rectangle(left, (x0, y0), (x0 + w, y0 + hh), (0, 0, 255), 2)
    cv2.putText(left, f"B seed {label}", (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    right = A.copy()
    if e["bl_BA"]:
        ax, ay, aw, ah, _ = e["bl_BA"]
        cv2.rectangle(right, (ax, ay), (ax + aw, ay + ah), (0, 255, 0), 2)
        cv2.putText(right, f"A hit {results[[r['label'] for r in results].index(label)]['peak_BA']}",
                    (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    if right.shape[0] < left.shape[0]:
        pad = np.full((left.shape[0] - right.shape[0], right.shape[1], 3), 25, np.uint8)
        right = np.vstack([right, pad])
    combo = np.hstack([left, right])
    cv2.imencode(".png", combo)[1].tofile(os.path.join(OV, f"recog_v2_{label}.png"))

json.dump(results, open(os.path.join(OUT, "v2_match.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("done")
