# -*- coding: utf-8 -*-
"""RANSAC 锚点标定：局部模板匹配取候选锚点 → RANSAC 单应 → 画 GT 验证。"""
import glob, json, os, random, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
import cv2, numpy as np
from clashlab.geo import Calib
from clashlab.assets import STATS
SPR = BASE + "/assets/clashking/buildings"
MAP = {"air-defense":"air_defense","x-bow":"x-bow","builder-hut":"builder's_hut",
       "multi-archer-tower":"multi-archer_tower","multi-gear-tower":"multi-gear_tower"}
def sprite(t):
    d = os.path.join(SPR, MAP.get(t, t.replace("-", "_")))
    if not os.path.isdir(d): return None
    fs = glob.glob(d + "/*.webp") + glob.glob(d + "/*.png")
    if not fs: return None
    fs.sort(key=lambda f: int(re.search(r"level_(\d+)", f).group(1)) if re.search(r"level_(\d+)", f) else 0)
    return cv2.imdecode(np.fromfile(fs[-1], np.uint8), cv2.IMREAD_UNCHANGED)
def quad0(ann, w):
    m = re.search(r"quad=\[\[([^\]]+)\],\[([^\]]+)\],\[([^\]]+)\],\[([^\]]+)\]\]", ann["note"] or "")
    if not m: return None
    q = np.array([[float(v) for v in g.split(",")] for g in m.groups()], np.float32)
    return q * (w / 2622.0)
def collect_anchors(img, ann, cal0):
    h, w = img.shape[:2]
    anchors = []
    for b in ann["buildings"]:
        t = b["type"]; spr = sprite(t)
        if spr is None: continue
        sx = int((STATS.get(t) or {}).get("size") or 2)
        gx, gy = b["tile"][0] + sx / 2.0, b["tile"][1] + sx / 2.0
        px, py = cal0.tile_to_px(gx, gy)
        R = 150
        x0, y0 = max(0, int(px - R)), max(0, int(py - R))
        x1, y1 = min(w, int(px + R)), min(h, int(py + R))
        roi = img[y0:y1, x0:x1]
        if roi.size == 0: continue
        best = None
        for sc in (0.35, 0.45, 0.55, 0.65, 0.8, 1.0):
            tw = max(8, int(spr.shape[1]*sc)); th = max(8, int(spr.shape[0]*sc))
            if tw >= roi.shape[1] or th >= roi.shape[0]: continue
            tpl = cv2.resize(spr[:, :, :3], (tw, th), interpolation=cv2.INTER_AREA)
            msk = cv2.resize(spr[:, :, 3], (tw, th), interpolation=cv2.INTER_NEAREST)
            res = cv2.matchTemplate(roi, tpl, cv2.TM_CCORR_NORMED, mask=msk)
            res = np.nan_to_num(res, nan=0.0, posinf=0.0, neginf=0.0)
            _, mx, _, ml = cv2.minMaxLoc(res)
            if best is None or mx > best[0]:
                best = (float(mx), x0 + ml[0] + tw/2.0, y0 + ml[1] + th/2.0)
        if best and best[0] > 0.72:
            anchors.append((gx, gy, best[1], best[2], best[0], t))
    return anchors
def ransac(anchors, iters=800, tol=10.0):
    if len(anchors) < 4: return None, []
    src = np.array([[a[0], a[1]] for a in anchors], np.float32)
    dst = np.array([[a[2], a[3]] for a in anchors], np.float32)
    best_inl = None
    rng = random.Random(7)
    for _ in range(iters):
        idx = rng.sample(range(len(anchors)), 4)
        H, _ = cv2.findHomography(src[idx], dst[idx], 0)
        if H is None: continue
        proj = cv2.perspectiveTransform(src.reshape(-1, 1, 2), H).reshape(-1, 2)
        err = np.linalg.norm(proj - dst, axis=1)
        inl = err < tol
        if best_inl is None or int(inl.sum()) > int(best_inl.sum()):
            best_inl = inl
    if best_inl is None or int(best_inl.sum()) < 4:
        return None, []
    H, _ = cv2.findHomography(src[best_inl], dst[best_inl], 0)
    return H, [a for a, k in zip(anchors, best_inl) if k]
PAIRS = [("01_annotated.json","b01.jpg"),("03_annotated.json","b02.jpg"),("04_annotated.json","b03.jpg"),
         ("05_annotated.json","b04.jpg"),("06_annotated.json","b05.jpg")]
outdir = BASE + "/out/layouts_src"
os.makedirs(outdir, exist_ok=True)
result = {}
for ann_name, img_name in PAIRS:
    ann = json.load(open(BASE + "/out/annotate/" + ann_name, encoding="utf-8"))
    img = cv2.imdecode(np.fromfile(BASE + "/android/assets/img/" + img_name, np.uint8), cv2.IMREAD_COLOR)
    q = quad0(ann, img.shape[1]); cal0 = Calib.from_quad(q, n=44)
    anchors = collect_anchors(img, ann, cal0)
    H, inl = ransac(anchors)
    print(img_name, "anchors", len(anchors), "inliers", len(inl), flush=True)
    if H is None:
        continue
    cal = Calib(H, n=44, quad=q)
    # 反算 quad：把 (0,0),(44,0),(44,44),(0,44) 投回像素
    quad_new = np.array([cal.tile_to_px(0,0), cal.tile_to_px(44,0), cal.tile_to_px(44,44), cal.tile_to_px(0,44)], np.float32)
    result[img_name] = {"quad": quad_new.tolist(), "inliers": len(inl), "anchors": len(anchors)}
    vis = img.copy()
    for b in ann["buildings"]:
        sx = int((STATS.get(b["type"]) or {}).get("size") or 2)
        p = cal.tile_to_px(b["tile"][0] + sx/2, b["tile"][1] + sx/2)
        cv2.circle(vis, (int(p[0]), int(p[1])), 5, (0, 0, 255), 2)
    cv2.imencode(".png", vis)[1].tofile(outdir + "/ransac_gt_" + img_name.replace(".jpg", ".png"))
json.dump(result, open(outdir + "/ransac_quads.json", "w"), ensure_ascii=False, indent=1)
print("saved ransac_quads.json + overlays", flush=True)
