# -*- coding: utf-8 -*-
"""战场 1080p 截图 → 标定（城墙 Hough）→ 门控候选 → 拼图批次。

用法：python tools/war_base_montage.py --image out/live/war1080/base_01_xxx.png [--thr 0.4]
"""
import argparse, glob, json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"

# 侦察界面相机固定：1280x720 手工标定，按宽度等比放大
QUAD_1280 = [[640.0, 52.0], [1120.0, 352.0], [640.0, 652.0], [178.0, 352.0]]


def default_quad(w):
    s = w / 1280.0
    return [[round(x * s, 1), round(y * s, 1)] for x, y in QUAD_1280]
sys.path.insert(0, BASE)
from clashlab.geo import Calib


def wall_quad(img):  # 备用：Hough 拟合（对真实阵可能不准，默认不用）
    h, w = img.shape[:2]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    white = cv2.inRange(hsv, (0, 0, 150), (180, 60, 255))
    orange = cv2.inRange(hsv, (8, 100, 120), (32, 255, 255))
    mask = cv2.bitwise_or(white, orange)
    mask[:80, :] = 0
    mask[:, :330] = 0
    mask[:, 1700:] = 0
    mask[900:, :] = 0
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    lines = cv2.HoughLinesP(mask, 1, np.pi / 180, threshold=80, minLineLength=120, maxLineGap=20)
    angles = []
    for l in (lines if lines is not None else [])[:400]:
        arr = np.asarray(l).reshape(-1)
        if arr.size < 4:
            continue
        x1, y1, x2, y2 = arr[:4]
        dx, dy = x2 - x1, y2 - y1
        if abs(dx) < 20 or abs(dy) < 12:
            continue
        a = np.degrees(np.arctan2(dy, dx))
        if 8 < abs(a) < 70:
            angles.append(a)
    if not angles:
        return None, None
    med = float(np.median([abs(a) for a in angles])); m = float(np.tan(np.radians(med)))
    ys, xs = np.nonzero(mask)
    c = ys - m * xs; d = ys + m * xs
    c1, c2 = np.percentile(c, 0.5), np.percentile(c, 99.5)
    d1, d2 = np.percentile(d, 0.5), np.percentile(d, 99.5)
    def inter(cv1, dv1):
        x = (dv1 - cv1) / (2 * m); return [float(x), float(m * x + cv1)]
    quad = np.float32([inter(c1, d1), inter(c1, d2), inter(c2, d2), inter(c2, d1)])
    return quad, med


def _nms(items, min_dist=1.6):
    """按置信度删除相邻重复候选（同一建筑只留一个）。"""
    out = []
    for it in items:
        x, y = it["tile"]
        if all(abs(x - o["tile"][0]) >= min_dist or abs(y - o["tile"][1]) >= min_dist for o in out):
            out.append(it)
    return out


def montage(img, quad, items, out_prefix, tag=""):
    cal = Calib.from_quad(quad, n=44)
    S, SCALE, PAD, COLS, ROWS = 96, 3, 22, 6, 4
    PER = COLS * ROWS
    items = _nms(items)
    made = []
    for b in range((len(items) + PER - 1) // PER):
        canvas = np.full((ROWS * (S*SCALE + PAD) + PAD, COLS * (S*SCALE + PAD) + PAD, 3), 32, np.uint8)
        for k in range(PER):
            i = b * PER + k
            if i >= len(items):
                break
            it = items[i]; x, y = it["tile"]; size = it["size"]
            # 至少裁 4x4 格，保证 96px 下边缘清晰
            side = max(4, size + 2)
            pad = (side - size) // 2
            x0 = max(0, x - pad); y0 = max(0, y - pad)
            x1 = min(44, x0 + side); y1 = min(44, y0 + side)
            x0 = max(0, x1 - side); y0 = max(0, y1 - side)
            p2 = [cal.tile_to_px(x0,y0), cal.tile_to_px(x1,y0), cal.tile_to_px(x1,y1), cal.tile_to_px(x0,y1)]
            H = cv2.getPerspectiveTransform(np.float32(p2), np.float32([[0,0],[S,0],[S,S],[0,S]]))
            crop = cv2.warpPerspective(img, H, (S, S), flags=cv2.INTER_AREA)
            crop = cv2.resize(crop, (S*SCALE, S*SCALE), interpolation=cv2.INTER_CUBIC)
            rr, cc = k // COLS, k % COLS
            y_ = PAD + rr * (S*SCALE + PAD); x_ = PAD + cc * (S*SCALE + PAD)
            canvas[y_:y_+S*SCALE, x_:x_+S*SCALE] = crop
            cv2.putText(canvas, "#%d" % (i + 1), (x_, y_ - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 220, 255), 1)
        out = "%s_%d.png" % (out_prefix, b + 1)
        cv2.imencode(".png", canvas)[1].tofile(out)
        made.append(out)
    return made


_FORCE_QUAD = None
_CHECK_HOUGH = False


def process(img_path, thr, outdir):
    from clashlab import auto_candidates as ac
    img = cv2.imdecode(np.fromfile(img_path, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return {"ok": False, "error": "read fail"}
    import argparse as _ap
    quad = None; ang = None
    if _FORCE_QUAD:
        quad = np.float32(_FORCE_QUAD); ang = 0.0
    else:
        quad = np.float32(default_quad(img.shape[1]))
        # 可选：Hough 结果作为参考输出
        try:
            _hq, _ang = wall_quad(img)
            ang = _ang
            if _hq is not None and _CHECK_HOUGH:
                quad = _hq
        except Exception:
            pass
    if quad is None:
        return {"ok": False, "error": "calib fail"}
    r = ac.candidates(img_path, quad.tolist(), max_n=90, gate_only=True, gate_threshold=thr, recall=True)
    items = r.get("items") or []
    name = os.path.splitext(os.path.basename(img_path))[0]
    os.makedirs(outdir, exist_ok=True)
    prefix = os.path.join(outdir, name)
    made = montage(img, quad, items, prefix) if items else []
    meta_path = prefix + "_candidates.json"
    try:
        import json as _json
        _json.dump({"image": img_path, "quad": np.asarray(quad).tolist(), "items": items},
                   open(meta_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    except Exception:
        meta_path = None
    return {"ok": True, "quad": quad.tolist(), "angle": ang, "items": len(items),
            "montages": [os.path.basename(m) for m in made], "meta": meta_path}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", default=None)
    ap.add_argument("--glob", default=None)
    ap.add_argument("--thr", type=float, default=0.40)
    ap.add_argument("--quad", default=None, help="四点 x,y;x,y;x,y;x,y 覆盖默认固定视角")
    ap.add_argument("--hough", action="store_true", help="改用 Hough 拟合（实验）")
    ap.add_argument("--outdir", default=os.path.join(BASE, "out", "labels", "war"))
    a = ap.parse_args()
    global _FORCE_QUAD, _CHECK_HOUGH
    if a.quad:
        _FORCE_QUAD = [[float(v) for v in part.split(",")] for part in a.quad.split(";")]
    _CHECK_HOUGH = bool(a.hough)
    imgs = [a.image] if a.image else sorted(glob.glob(a.glob or os.path.join(BASE, "out", "live", "war1080", "base_*.png")))
    for p in imgs:
        res = process(p, a.thr, a.outdir)
        print(os.path.basename(p), "->", json.dumps(res, ensure_ascii=False)[:220], flush=True)


if __name__ == "__main__":
    main()
