# -*- coding: utf-8 -*-
# v10_quad.py — 可见草地边界拟合（仅底/左/右可见，顶出画）。HSV草色掩膜 + RANSAC 直线。
import cv2, numpy as np, os, json
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
FULL = os.path.join(ROOT, "out", "overlay", "full")
im = cv2.imdecode(np.fromfile(os.path.join(FULL, "b00.png"), dtype=np.uint8), cv2.IMREAD_COLOR)
H, W = im.shape[:2]
hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
# 草色：亮绿，G 主导
b, g, r = cv2.split(im)
grass = ((g.astype(int) > r.astype(int) + 18) & (g.astype(int) > b.astype(int) + 8) & (g > 90)).astype(np.uint8) * 255
grass = cv2.morphologyEx(grass, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
cv2.imencode(".png", grass)[1].tofile(os.path.join(FULL, "raw", "grass_mask.png"))

def ransac_line(pts, iters=400, tol=4):
    best = None
    pts = np.array(pts)
    if len(pts) < 10:
        return None
    for _ in range(iters):
        i, j = np.random.choice(len(pts), 2, replace=False)
        p1, p2 = pts[i], pts[j]
        d = p2 - p1
        n = np.hypot(*d) + 1e-9
        rel = pts - p1
        dist = np.abs(d[0]*rel[:, 1] - d[1]*rel[:, 0]) / n
        inl = pts[dist < tol]
        if best is None or len(inl) > len(best[1]):
            best = ((p1, p2), inl)
    return best

# 底边：下半部，草→非草过渡的最下点
edges = []
for y in range(int(H*0.55), H):
    row = grass[y]
    xs = np.where(row > 0)[0]
    if len(xs) > 20:
        # 该段草的最右/最左极端点
        edges.append((xs[0], y)); edges.append((xs[-1], y))
# 左侧：左部，草→水过渡
for x in range(0, int(W*0.30)):
    col = grass[:, x]
    ys = np.where(col > 0)[0]
    if len(ys) > 20:
        edges.append((x, ys[0])); edges.append((x, ys[-1]))

res = {}
for name, region in [("bottom", [e for e in edges if e[1] > H*0.55]),
                     ("left", [e for e in edges if e[0] < W*0.30])]:
    fit = ransac_line(region)
    if fit:
        (p1, p2), inl = fit
        res[name] = {"p1": p1.tolist(), "p2": p2.tolist(), "n_inl": len(inl)}
print(json.dumps(res, ensure_ascii=False, indent=1))

vis = im.copy()
for name, d in res.items():
    cv2.line(vis, tuple(d["p1"]), tuple(d["p2"]), (0, 0, 255), 2)
cv2.imencode(".png", vis)[1].tofile(os.path.join(FULL, "raw", "quad_visible.png"))
json.dump(res, open(os.path.join(FULL, "raw", "quad_visible.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
