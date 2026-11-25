# -*- coding: utf-8 -*-
# recog_match.py — 跨块 NCC 跨帧识别（块A抠模板 -> 全部块搜；纯离线）
# 判据：命中峰数(全局去重后) ≈ 目视普查应有实例数；弃用 peak/次峰比。
import json, os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BLK = os.path.join(ROOT, "out", "overlay", "blocks")
OUTIMG = os.path.join(ROOT, "out", "overlay")
os.makedirs(OUTIMG, exist_ok=True)
log = json.load(open(os.path.join(BLK, "collect_log.json"), encoding="utf-8"))
off = {t["file"]: (t["cx"], t["cy"]) for t in log["tiles"]}

blocks = {}
for t in log["tiles"]:
    blocks[t["file"].replace(".png", "")] = cv2.imdecode(
        np.fromfile(os.path.join(BLK, t["file"]), dtype=np.uint8), cv2.IMREAD_COLOR)
    off[t["file"].replace(".png", "")] = off.pop(t["file"])

# seed: label, 模板来源块, (x,y,w,h), 目视普查可见实例数, 足迹半径(px)
SEEDS = [
    ("法师塔_wizard",      "b09", (420, 90, 360, 380), 1, 90),
    ("迫击炮_mortar",     "b09", (160, 30, 300, 250), 1, 80),
    ("X连弩_xbow",        "b11", (560, 120, 320, 220), 1, 80),
    ("空气炮_dome",       "b10", (0, 20, 300, 320), 1, 80),
    ("红金棘塔_待考",      "b04", (380, 250, 330, 290), 1, 80),
    ("四锥塔_待考",       "b11", (100, 0, 320, 260), 1, 80),
    ("紫金塔_待考",       "b13", (0, 110, 210, 440), 1, 90),
    ("白堡塔_待考",       "b05", (350, 120, 260, 320), 1, 80),
]
SCALES = [0.92, 1.0, 1.08]
THRESH = 0.78

def gray(im):
    return cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)

def nms_local(pts, resp, minr):
    # pts: list of (x,y,score); 块内非极大抑制
    order = np.argsort(-np.array(resp))
    keep = []
    for i in order:
        x, y, s = pts[i]
        if all((x - kx) ** 2 + (y - ky) ** 2 > (minr * 1.4) ** 2 for kx, ky, _ in keep):
            keep.append((x, y, s))
    return keep

results = {}
for label, src, box, expect, rad in SEEDS:
    sx, sy, sw, sh = box
    tpl = blocks[src][sy:sy + sh, sx:sx + sw]
    tg = gray(tpl)
    global_hits = []  # (gx, gy, score, block)
    best = -1.0
    for fn, im in blocks.items():
        g = gray(im)
        ox, oy = off[fn]
        for sc in SCALES:
            tw, th = max(8, int(sw * sc)), max(8, int(sh * sc))
            if tw >= g.shape[1] or th >= g.shape[0]:
                continue
            tsc = cv2.resize(tg, (tw, th), interpolation=cv2.INTER_AREA if sc < 1 else cv2.INTER_CUBIC)
            res = cv2.matchTemplate(g, tsc, cv2.TM_CCOEFF_NORMED)
            # 块内 NMS
            flat = res.ravel()
            idx = np.where(flat >= THRESH)[0]
            cand = []
            for ii in idx:
                yy, xx = divmod(ii, res.shape[1])
                cand.append((xx, yy, float(flat[ii])))
            keep = nms_local(cand, [c[2] for c in cand], rad)
            for x, y, s in keep:
                if s > best:
                    best = s
                global_hits.append((ox + x + tw // 2, oy + y + th // 2, s, fn, sc))
    # 全局去重：40px 簇
    global_hits.sort(key=lambda h: -h[2])
    clusters = []
    for hx, hy, s, fn, sc in global_hits:
        placed = False
        for cl in clusters:
            cx, cy = cl[0]
            if (hx - cx) ** 2 + (hy - cy) ** 2 < 45 ** 2:
                cl[1].append((hx, hy, s, fn, sc))
                if s > cl[2]:
                    cl[0] = [hx, hy]; cl[2] = s
                placed = True
                break
        if not placed:
            clusters.append([[hx, hy], [(hx, hy, s, fn, sc)], s])
    results[label] = {
        "src": src, "expect": expect, "peak": round(best, 4),
        "raw_hits": len(global_hits), "instances": len(clusters),
        "clusters": [[(round(c[0][0], 1), round(c[0][1], 1)), round(c[2], 4),
                      sorted({m[3] for m in c[1]})] for c in clusters],
    }
    r = results[label]
    verdict = "过" if abs(r["instances"] - expect) <= max(1, expect * 0.5) and r["peak"] >= THRESH else "不过"
    r["verdict"] = verdict
    print(f"{label}: peak={r['peak']} raw={r['raw_hits']} inst={r['instances']} expect={expect} -> {verdict}")

json.dump(results, open(os.path.join(ROOT, "tools", "base_out", "recog_raw.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("done")
