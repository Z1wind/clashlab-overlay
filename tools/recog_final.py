# -*- coding: utf-8 -*-
# recog_final.py — 最终跨帧识别：块A抠紧框模板 -> 全部块多尺度NCC；
# 排除自匹配；判据=全局去重后命中实例数≈目视普查应有数；弃 peak/次峰比。
# 纯离线：只读 blocks/，写 out/overlay 与 out/recog。
import json, os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BLK = os.path.join(ROOT, "out", "overlay", "blocks")
OV = os.path.join(ROOT, "out", "overlay")
RCG = os.path.join(ROOT, "out", "recog")
os.makedirs(RCG, exist_ok=True)

log = json.load(open(os.path.join(BLK, "collect_log.json"), encoding="utf-8"))
blocks = {}
for t in log["tiles"]:
    blocks[t["file"].replace(".png", "")] = cv2.imdecode(
        np.fromfile(os.path.join(BLK, t["file"]), dtype=np.uint8), cv2.IMREAD_COLOR)

# label, 种子块, 紧框(x,y,w,h), 目视普查可见实例数, 足迹半径px, 类型归属备注
SEEDS = [
    ("法师塔",      "b10", (300, 190, 380, 340), 1, 95, "gray body/green banners, wizard on roof"),
    ("迫击炮",      "b09", (190, 50, 260, 200), 1, 80, "black barrel on red lava pad"),
    ("X连弩",       "b11", (600, 140, 260, 190), 1, 80, "crossbow on gold/red mount"),
    ("空气炮",      "b10", (0, 40, 260, 280),   1, 80, "transparent dome fan (疑似)"),
    ("红金棘塔_待考", "b04", (430, 280, 240, 260), 1, 80, "black/gold spiked, red-ring crown; 外观未定名"),
    ("四锥塔_待考",  "b11", (150, 20, 250, 240), 1, 80, "4 checkerboard horns; 外观未定名"),
    ("紫金塔_待考",  "b13", (10, 130, 180, 380), 1, 90, "dark purple+gold spire; 外观未定名"),
    ("白堡塔_待考",  "b05", (370, 150, 220, 270), 1, 80, "white octagonal tower on purple base"),
    ("加农炮_locked", "b14", (770, 50, 180, 200), 1, 70, "gray barrel under lock/upgrade"),
    ("链锅_待考",    "b09", (240, 340, 260, 210), 1, 70, "chained flaming cauldron; 外观未定名"),
]
SCALES = [0.92, 1.0, 1.08]
HIT = 0.60       # 跨帧命中下限（自匹配已排除）
REPEAT = 0.65    # 跨帧重复证据线

def prep(im):
    return cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)

def nms_keep(cand, minr):
    cand = sorted(cand, key=lambda c: -c[2])
    keep = []
    for x, y, s, fn, sc in cand:
        if all((x - kx) ** 2 + (y - ky) ** 2 > (minr * 1.5) ** 2 for kx, ky, *_ in keep):
            keep.append((x, y, s, fn, sc))
    return keep

rows = []
evidence = {}
for label, src, box, expect, rad, note in SEEDS:
    sx, sy, sw, sh = box
    tpl = prep(blocks[src])[sy:sy + sh, sx:sx + sw]
    cand = []
    best = -1.0; best_hit = None
    for fn, im in blocks.items():
        if fn == src:
            continue
        g = prep(im)
        for sc in SCALES:
            tw, th = max(8, int(sw * sc)), max(8, int(sh * sc))
            if tw >= g.shape[1] or th >= g.shape[0]:
                continue
            tsc = cv2.resize(tpl, (tw, th), interpolation=cv2.INTER_AREA if sc < 1 else cv2.INTER_CUBIC)
            res = cv2.matchTemplate(g, tsc, cv2.TM_CCOEFF_NORMED)
            _, mx, _, ml = cv2.minMaxLoc(res)
            if mx > best:
                best, best_hit = float(mx), (fn, ml, tw, th, sc, float(mx))
            ys, xs = np.where(res >= HIT)
            for y, x in zip(ys, xs):
                cand.append((int(x), int(y), float(res[y, x]), fn, sc))
    keep = nms_keep(cand, rad)
    # 全局去重簇（无放置偏移可靠，仅按块内保留 + 计数）
    inst = len({(k[3], round(k[0] / 50), round(k[1] / 50)) for k in keep})
    peak = round(best, 4)
    cross_ok = peak >= REPEAT
    ok = cross_ok and abs(inst - expect) <= max(1, expect)
    verdict = "过" if ok else ("边缘" if peak >= HIT else "不过")
    rows.append(dict(label=label, src=src, expect=expect, peak=peak,
                     hits=len(keep), inst=inst, verdict=verdict, note=note,
                     best_neighbor=best_hit[0] if best_hit else None,
                     best_loc=best_hit[1] if best_hit else None))
    evidence[label] = dict(best=best_hit, keep=keep, box=box, src=src)
    print(f"{label}: peak={peak} hits={len(keep)} inst={inst} expect={expect} -> {verdict}")

# ---- 证据图：左=种子块(模板框) 右=最佳邻块(命中框) ----
for label, ev in evidence.items():
    src = ev["src"]; sx, sy, sw, sh = ev["box"]
    left = blocks[src].copy()
    cv2.rectangle(left, (sx, sy), (sx + sw, sy + sh), (0, 255, 0), 3)
    cv2.putText(left, f"seed {src}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
    bh = ev["best"]
    right = np.full_like(blocks[src], 30)
    if bh:
        fn, ml, tw, th, sc, _ncc = bh
        right = blocks[fn].copy()
        x, y = ml
        cv2.rectangle(right, (x, y), (x + tw, y + th), (0, 0, 255), 3)
        cv2.putText(right, f"best {fn} ncc={round(ev['best'][5], 4)}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    combo = np.hstack([left, right])
    safe = label.replace("/", "_")
    cv2.imencode(".png", combo)[1].tofile(os.path.join(OV, f"recog_{safe}.png"))

json.dump(rows, open(os.path.join(RCG, "recog_rows.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("done")
