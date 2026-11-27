# -*- coding: utf-8 -*-
"""用 ClashKing 立绘在渲染阵图 b01(war_138) 上做模板匹配，与手工标注对比。"""
import glob, json, os, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab.geo import Calib
IMG = os.path.join(BASE, "android", "assets", "img", "b01.jpg")
SPR = os.path.join(BASE, "assets", "clashking", "buildings")
ANN = os.path.join(BASE, "out", "annotate", "01_annotated.json")

MAP = {
 "air-defense": "air_defense", "x-bow": "x-bow", "builder-hut": "builder's_hut",
 "multi-archer-tower": "multi-archer_tower", "multi-gear-tower": "multi-gear_tower",
}

def dir_for(t):
    if t in MAP: return MAP[t]
    return t.replace("-", "_")

img = cv2.imdecode(np.fromfile(IMG, np.uint8), cv2.IMREAD_COLOR)
h, w = img.shape[:2]
ann = json.load(open(ANN, encoding="utf-8"))
note = ann.get("note") or ""
m = re.search(r"quad=\[\[([^\]]+)\],\[([^\]]+)\],\[([^\]]+)\],\[([^\]]+)\]\]", note)
q = np.array([[float(v) for v in g.split(",")] for g in m.groups()], np.float32) if m else None
scale = w / 2622.0
quad = q * scale
cal = Calib.from_quad(quad, n=44)
print("img", img.shape, "quad", np.round(quad, 1).tolist())

def tile_of(px, py):
    # 用 Calib 反解：搜索网格 uv 的逆双线性
    def bil(u, v):
        p = [cal.tile_to_px(x, y) for x, y in ((0, 0))]
    return None

# 简单反解：在 44x44 上找最近格（用 quad 双线性逆变换）
def inv_quad(px, py):
    p = np.float32([[0,0],[44,0],[44,44],[0,44]])
    H = cv2.getPerspectiveTransform(quad.astype(np.float32), p)
    pt = cv2.perspectiveTransform(np.float32([[[px, py]]]), H)[0][0]
    return float(pt[0]), float(pt[1])

gt = [(b["type"], b["tile"][0], b["tile"][1]) for b in ann["buildings"]]
print("GT buildings:", len(gt), "types:", len({t for t,_,_ in gt}))

def load_sprite(t):
    d = os.path.join(SPR, dir_for(t))
    if not os.path.isdir(d):
        return None
    files = glob.glob(os.path.join(d, "*.webp")) + glob.glob(os.path.join(d, "*.png"))
    if not files:
        return None
    def lvl(f):
        mm = re.search(r"level_(\d+)", f)
        return int(mm.group(1)) if mm else 0
    files.sort(key=lvl)
    return cv2.imdecode(np.fromfile(files[-1], np.uint8), cv2.IMREAD_UNCHANGED)

detections = []
for t in sorted({g[0] for g in gt}):
    spr = load_sprite(t)
    if spr is None or spr.ndim != 3 or spr.shape[2] != 4:
        print("skip", t, None if spr is None else spr.shape)
        continue
    best = []
    for sc in (0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 1.0, 1.15):
        tw = max(8, int(spr.shape[1] * sc)); th = max(8, int(spr.shape[0] * sc))
        if tw >= w or th >= h: continue
        tpl = cv2.resize(spr[:, :, :3], (tw, th), interpolation=cv2.INTER_AREA)
        msk = cv2.resize(spr[:, :, 3], (tw, th), interpolation=cv2.INTER_NEAREST)
        res = cv2.matchTemplate(img, tpl, cv2.TM_CCORR_NORMED, mask=msk)
        res = np.nan_to_num(res, nan=0.0, posinf=0.0, neginf=0.0)
        for _ in range(2):
            _min, mx, _minl, ml = cv2.minMaxLoc(res)
            if mx < 0.72: break
            cx, cy = ml[0] + tw / 2.0, ml[1] + th / 2.0
            tx, ty = inv_quad(cx, cy)
            best.append({"type": t, "score": float(mx), "tile": [round(tx - 0.5), round(ty - 0.5)], "scale": sc})
            x0, y0 = max(0, ml[0] - tw // 2), max(0, ml[1] - th // 2)
            res[y0:ml[1] + th // 2, x0:ml[0] + tw // 2] = 0
    # NMS
    best.sort(key=lambda d: -d["score"])
    keep = []
    for d in best:
        if all(abs(d["tile"][0] - k["tile"][0]) > 1.2 or abs(d["tile"][1] - k["tile"][1]) > 1.2 for k in keep):
            keep.append(d)
    detections.extend(keep)
    print("type", t, "det:", len(keep))

# 评估：GT 是否有正确类型检测（±1.5 格）；检测是否命中 GT
matched_gt = set()
tp = 0
for d in detections:
    for i, (t, x, y) in enumerate(gt):
        if i in matched_gt: continue
        if t == d["type"] and abs(x - d["tile"][0]) <= 1.5 and abs(y - d["tile"][1]) <= 1.5:
            matched_gt.add(i); tp += 1; break
print("DETECTIONS:", len(detections), "TP:", tp, "precision:", round(tp / max(1, len(detections)), 3),
      "recall:", round(len(matched_gt) / max(1, len(gt)), 3), "GT:", len(gt))
json.dump({"detections": detections, "gt": gt}, open(os.path.join(BASE, "out", "layouts_src", "tm_eval_b01.json"), "w"),
          ensure_ascii=False, indent=1)
# 可视化
vis = img.copy()
for d in detections:
    cx, cy = cal.tile_to_px(d["tile"][0] + 0.5, d["tile"][1] + 0.5)
    cv2.circle(vis, (int(cx), int(cy)), 6, (0, 200, 255), 2)
    cv2.putText(vis, d["type"][:10], (int(cx) + 7, int(cy)), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 200, 255), 1)
cv2.imencode(".png", vis)[1].tofile(os.path.join(BASE, "out", "layouts_src", "tm_overlay_b01.png"))
print("saved overlay")
