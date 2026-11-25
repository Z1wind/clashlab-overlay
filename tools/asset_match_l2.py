# -*- coding: utf-8 -*-
# asset_match_l2.py — 最大档分块(b00..b14) alpha-mask 匹配；bandA 0.60-1.40 步0.05
# 输出 out/recog/asset_raw_l2.json（每类 best peak / 跨块 NMS 后命中 / 最优尺度 / 模板）
import os, json, time, cv2, numpy as np, sys

ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
MAN = os.path.join(ROOT, "assets", "coc", "buildings", "manifest_buildings.json")
RECORD = os.path.join(ROOT, "out", "recog")
BLKDIR = os.path.join(ROOT, "out", "overlay", "blocks")
THR = 0.75; NMS_IOU = 0.3; TOPK = 6; MAXKEEP = 30
SCALES = np.round(np.arange(0.60, 1.401, 0.05), 3)

def load_img(p):
    return cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_COLOR)

def load_tpl(p):
    im = cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if im is None or im.ndim != 3 or im.shape[2] != 4:
        return None
    bgr = im[:, :, :3]; a = im[:, :, 3]
    ys, xs = np.where(a > 40)
    if len(xs) < 20:
        return None
    return bgr[ys.min():ys.max()+1, xs.min():xs.max()+1], a[ys.min():ys.max()+1, xs.min():xs.max()+1]

def nms(boxes, scores, iou_thr=NMS_IOU):
    if not boxes: return []
    idx = np.argsort(-np.array(scores)); keep = []
    while len(idx):
        i = idx[0]; keep.append(int(i)); rest = idx[1:]
        if len(rest) == 0: break
        b = boxes[i]; br = np.array(boxes)[rest]
        ix0 = np.maximum(b[0], br[:,0]); iy0 = np.maximum(b[1], br[:,1])
        ix1 = np.minimum(b[2], br[:,2]); iy1 = np.minimum(b[3], br[:,3])
        inter = np.maximum(0,ix1-ix0)*np.maximum(0,iy1-iy0)
        uni = (b[2]-b[0])*(b[3]-b[1])+(br[:,2]-br[:,0])*(br[:,3]-br[:,1])-inter
        iou = inter/np.maximum(uni,1)
        idx = rest[iou <= iou_thr]
    return keep

def main():
    man = json.load(open(MAN, encoding="utf-8"))
    groups = {}
    for e in man["entries"]:
        groups.setdefault(e["type"], []).append(e)
    blocks = [f"b{i:02d}.png" for i in range(15)]
    # 预载模板
    tpl_cache = {}
    for ttype, entries in groups.items():
        tpl_cache[ttype] = []
        for e in entries:
            L = load_tpl(os.path.join(ROOT, e["file"].replace("/", os.sep)))
            if L:
                tpl_cache[ttype].append((e, L[0], L[1]))
    results = {}
    t0 = time.time()
    for ttype in sorted(groups):
        cands = []; gmax = 0.0; sat = 0.0; nc = 0
        for b in blocks:
            img = load_img(os.path.join(BLKDIR, b))
            H, W = img.shape[:2]
            for e, bgr, mask in tpl_cache[ttype]:
                th0, tw0 = bgr.shape[:2]
                for s in SCALES:
                    tw = max(14, int(round(tw0*s))); th = max(14, int(round(th0*s)))
                    if tw > W-4 or th > H-4: continue
                    t = cv2.resize(bgr, (tw, th), interpolation=cv2.INTER_AREA)
                    m = cv2.resize(mask, (tw, th), interpolation=cv2.INTER_AREA)
                    res = cv2.matchTemplate(img, t, cv2.TM_CCORR_NORMED, mask=m)
                    gmax = max(gmax, float(res.max()))
                    sat += float((res >= THR).mean()); nc += 1
                    dil = cv2.dilate(res, np.ones((9, 9), np.uint8))
                    ys, xs = np.where((res == dil) & (res >= THR))
                    if len(xs) == 0: continue
                    vals = res[ys, xs]
                    for j in np.argsort(-vals)[:TOPK]:
                        y, x = int(ys[j]), int(xs[j])
                        cands.append([float(vals[j]), b, x, y, x+tw, y+th, float(s), e["file"]])
            # 每块内 NMS 已可省，跨块后统一 NMS（块间不重叠坐标体系不同，先按块内压）
        if cands:
            boxes = [[c[2], c[3], c[4], c[5]] for c in cands]
            keep = nms(boxes, [c[0] for c in cands])
            kept = [cands[i] for i in keep]
            kept.sort(key=lambda c: -c[0]); kept = kept[:MAXKEEP]
        else:
            kept = []
        results[ttype] = {
            "best_peak": round(kept[0][0], 4) if kept else None,
            "global_max": round(gmax, 4),
            "sat_frac75": round(sat/max(nc,1), 4),
            "best_scale": kept[0][6] if kept else None,
            "best_tpl": kept[0][7] if kept else None,
            "n_hits": len(kept),
            "hits": [{"score": round(c[0],4), "block": c[1], "x0": c[2], "y0": c[3],
                      "x1": c[4], "y1": c[5], "scale": c[6], "tpl": c[7]} for c in kept],
        }
        print(f"{ttype:14s} peak={results[ttype]['best_peak']} gmax={results[ttype]['global_max']} "
              f"sat={results[ttype]['sat_frac75']} hits={len(kept)} s={results[ttype]['best_scale']}", flush=True)
    print("elapsed", round(time.time()-t0), "s", flush=True)
    json.dump({"band": [0.60, 1.40], "step": 0.05, "thr": THR, "results": results},
              open(os.path.join(RECORD, "asset_raw_l2.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
