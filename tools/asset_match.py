# -*- coding: utf-8 -*-
# asset_match.py — 官方 RGBA 素材 alpha-mask 多尺度匹配（纯离线，只读素材/输入图）
# 用法: python asset_match.py <tag> [scale_lo scale_hi]
# 结果写 out/recog/asset_raw_<tag>.json
import os, sys, json, time, cv2, numpy as np

ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
MAN = os.path.join(ROOT, "assets", "coc", "buildings", "manifest_buildings.json")
RECORD = os.path.join(ROOT, "out", "recog")

THR = 0.75
NMS_IOU = 0.3
TOPK_PER_CELL = 8      # 每个(模板,尺度)只留 top-k 峰
MAX_KEEP = 40          # NMS 后每类最多保留框

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
    x0, x1, y0, y1 = xs.min(), xs.max()+1, ys.min(), ys.max()+1
    return bgr[y0:y1, x0:x1], a[y0:y1, x0:x1]

def nms(boxes, scores, iou_thr=NMS_IOU):
    if not boxes:
        return []
    idx = np.argsort(-np.array(scores))
    keep = []
    while len(idx):
        i = idx[0]; keep.append(int(i))
        rest = idx[1:]
        if len(rest) == 0:
            break
        b = boxes[i]; br = np.array(boxes)[rest]
        ix0 = np.maximum(b[0], br[:, 0]); iy0 = np.maximum(b[1], br[:, 1])
        ix1 = np.minimum(b[2], br[:, 2]); iy1 = np.minimum(b[3], br[:, 3])
        iw = np.maximum(0, ix1-ix0); ih = np.maximum(0, iy1-iy0)
        inter = iw*ih
        uni = (b[2]-b[0])*(b[3]-b[1]) + (br[:,2]-br[:,0])*(br[:,3]-br[:,1]) - inter
        iou = inter/np.maximum(uni, 1)
        idx = rest[iou <= iou_thr]
    return keep

def run_image(tag, img, off, scale_lo=0.20, scale_hi=1.60):
    H, W = img.shape[:2]
    man = json.load(open(MAN, encoding="utf-8"))
    groups = {}
    for e in man["entries"]:
        groups.setdefault(e["type"], []).append(e)
    scales = np.round(np.arange(scale_lo, scale_hi+0.001, 0.03), 3)
    results = {}
    t0 = time.time()
    for ttype, entries in sorted(groups.items()):
        cands = []
        gmax = 0.0; frac75 = 0; ncells = 0
        for e in entries:
            tp = os.path.join(ROOT, e["file"].replace("/", os.sep))
            loaded = load_tpl(tp)
            if loaded is None:
                continue
            bgr, mask = loaded
            th0, tw0 = bgr.shape[:2]
            for s in scales:
                tw = max(14, int(round(tw0*s))); th = max(14, int(round(th0*s)))
                if tw > W-4 or th > H-4:
                    continue
                t = cv2.resize(bgr, (tw, th), interpolation=cv2.INTER_AREA)
                m = cv2.resize(mask, (tw, th), interpolation=cv2.INTER_AREA)
                res = cv2.matchTemplate(img, t, cv2.TM_CCORR_NORMED, mask=m)
                gmax = max(gmax, float(res.max()))
                # 饱和度证据：>=0.75 的像素占比（每尺度采样均值）
                frac75 += float((res >= THR).mean()); ncells += 1
                # 局部峰 top-k
                dil = cv2.dilate(res, np.ones((9, 9), np.uint8))
                ys, xs = np.where((res == dil) & (res >= THR))
                if len(xs) == 0:
                    continue
                vals = res[ys, xs]
                order = np.argsort(-vals)[:TOPK_PER_CELL]
                for j in order:
                    y, x = int(ys[j]), int(xs[j])
                    cands.append([float(vals[j]), int(x)+off[0], int(y)+off[1],
                                  int(x+tw)+off[0], int(y+th)+off[1],
                                  float(s), e["file"]])
        if cands:
            boxes = [[c[1], c[2], c[3], c[4]] for c in cands]
            scores = [c[0] for c in cands]
            keep = nms(boxes, scores)
            kept = [cands[i] for i in keep]
            kept.sort(key=lambda c: -c[0])
            kept = kept[:MAX_KEEP]
        else:
            kept = []
        results[ttype] = {
            "best_peak": round(kept[0][0], 4) if kept else None,
            "global_max": round(gmax, 4),
            "saturation_frac75": round(frac75/max(ncells, 1), 4),
            "best_scale": kept[0][5] if kept else None,
            "best_tpl": kept[0][6] if kept else None,
            "n_hits": len(kept),
            "hits": [{"score": round(c[0], 4), "x0": c[1], "y0": c[2],
                      "x1": c[3], "y1": c[4], "scale": c[5], "tpl": c[6]}
                     for c in kept],
        }
        bp = results[ttype]["best_peak"]
        print(f"  {ttype:14s} peak={bp} gmax={results[ttype]['global_max']} "
              f"sat={results[ttype]['saturation_frac75']} hits={len(kept)}", flush=True)
    print(f"[{tag}] elapsed {time.time()-t0:.0f}s", flush=True)
    return results

IMGS = {
    "b14": (r"out\overlay\enemy\b14_full.png", None),
    "w14": (r"bases\th16\war_20261123\14_kekejdj.png", (15, 35, 1024, 585)),
    "w15": (r"bases\th16\war_20261123\15_qembzi.png", (15, 48, 1028, 602)),
    "w16": (r"bases\th16\war_20261123\16_diddieyang.png", (15, 48, 1027, 599)),
    "w17": (r"bases\th16\war_20261123\17_akib.png", (15, 46, 1021, 596)),
}

def main():
    tag = sys.argv[1]
    lo = float(sys.argv[2]) if len(sys.argv) > 2 else 0.20
    hi = float(sys.argv[3]) if len(sys.argv) > 3 else 1.60
    if tag not in IMGS:
        print("unknown", tag); return
    path, bounds = IMGS[tag]
    img = load_img(os.path.join(ROOT, path))
    off = (0, 0)
    if bounds:
        L, T, R, B = bounds
        off = (L, T)
        img = img[T:B, L:R]
    print(f"[{tag}] {img.shape[1]}x{img.shape[0]} scales {lo}-{hi}", flush=True)
    results = run_image(tag, img, off, lo, hi)
    out = os.path.join(RECORD, f"asset_raw_{tag}.json")
    json.dump({"tag": tag, "image": path, "scale_range": [lo, hi],
               "step": 0.03, "thr": THR, "results": results},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("saved", out, flush=True)

if __name__ == "__main__":
    main()
